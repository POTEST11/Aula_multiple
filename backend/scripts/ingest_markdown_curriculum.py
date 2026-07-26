"""Ingest markdown DBA files into curriculum_embeddings for RAG baseline.

Processes .md files from a directory, extracts metadata from the file header,
chunks the content by DBA sections, generates embeddings, and stores them
in the curriculum_embeddings table with deduplication by content_hash.

Usage:
    python scripts/ingest_markdown_curriculum.py --dir /app/curriculum_data
"""

import asyncio
import hashlib
import logging
import re
import sys
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent to path for app imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.dependencies import async_session_factory  # noqa: E402
from app.models.curriculum_embedding import CurriculumEmbedding  # noqa: E402
from app.rag.embeddings import EmbeddingService  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_metadata(content: str) -> dict:
    """Extract metadata from the markdown header."""
    metadata = {}
    meta_match = re.search(r"## Metadata\n(.*?)(?=\n##|\n---)", content, re.DOTALL)
    if meta_match:
        for line in meta_match.group(1).strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip("- ").strip()
                metadata[key] = value.strip()
    return metadata


def chunk_by_dba(content: str, subject: str, country: str) -> list[dict]:
    """Split markdown content into chunks by DBA section.

    Each chunk contains one DBA with its grade context.
    """
    chunks = []
    current_grade = None

    # Split by grade headers (## Grado X)
    grade_pattern = re.compile(r"^## Grado (\d+)", re.MULTILINE)
    dba_pattern = re.compile(r"^### (DBA \d+\.\d+.*?)$", re.MULTILINE)

    lines = content.split("\n")
    current_chunk_lines = []
    current_dba_title = None

    for line in lines:
        grade_match = grade_pattern.match(line)
        if grade_match:
            # Save previous chunk if exists
            if current_chunk_lines and current_grade:
                chunk_text = "\n".join(current_chunk_lines).strip()
                if chunk_text and len(chunk_text) > 20:
                    chunks.append({
                        "content": chunk_text,
                        "grade": int(current_grade),
                        "subject": subject,
                        "country": country,
                    })
            current_grade = grade_match.group(1)
            current_chunk_lines = []
            current_dba_title = None
            continue

        dba_match = dba_pattern.match(line)
        if dba_match and current_grade:
            # Save previous DBA chunk
            if current_chunk_lines:
                chunk_text = "\n".join(current_chunk_lines).strip()
                if chunk_text and len(chunk_text) > 20:
                    chunks.append({
                        "content": chunk_text,
                        "grade": int(current_grade),
                        "subject": subject,
                        "country": country,
                    })
            current_chunk_lines = [line]
            current_dba_title = dba_match.group(1)
        elif current_grade:
            current_chunk_lines.append(line)

    # Don't forget the last chunk
    if current_chunk_lines and current_grade:
        chunk_text = "\n".join(current_chunk_lines).strip()
        if chunk_text and len(chunk_text) > 20:
            chunks.append({
                "content": chunk_text,
                "grade": int(current_grade),
                "subject": subject,
                "country": country,
            })

    return chunks


async def ingest_file(file_path: Path, embedding_service: EmbeddingService) -> int:
    """Process a single .md file and store embeddings."""
    logger.info(f"Processing: {file_path.name}")

    content = file_path.read_text(encoding="utf-8")
    metadata = parse_metadata(content)

    country = metadata.get("pais", "Colombia")
    subject = metadata.get("materia", file_path.stem.replace("_", " ").title())

    # Chunk by DBA sections
    chunks = chunk_by_dba(content, subject, country)
    logger.info(f"  Found {len(chunks)} chunks for {subject}")

    if not chunks:
        logger.warning(f"  No chunks found in {file_path.name}")
        return 0

    # Generate embeddings in batch
    texts = [c["content"] for c in chunks]
    embeddings = await embedding_service.generate_batch(texts)

    # Store in DB with deduplication
    stored = 0
    async with async_session_factory() as session:
        for chunk, embedding in zip(chunks, embeddings):
            content_hash = hashlib.sha256(chunk["content"].encode()).hexdigest()

            # Check if already exists
            existing = await session.execute(
                select(CurriculumEmbedding).where(
                    CurriculumEmbedding.content_hash == content_hash
                )
            )
            if existing.scalar_one_or_none():
                continue

            record = CurriculumEmbedding(
                country=chunk["country"],
                grade=chunk["grade"],
                subject=chunk["subject"],
                content=chunk["content"],
                content_hash=content_hash,
                embedding=embedding,
                metadata={"source": file_path.name},
            )
            session.add(record)
            stored += 1

        await session.commit()

    logger.info(f"  Stored {stored} new embeddings ({len(chunks) - stored} duplicates skipped)")
    return stored


async def main():
    """Main entry point: process all .md files in the curriculum directory."""
    import argparse

    parser = argparse.ArgumentParser(description="Ingest markdown DBA files")
    parser.add_argument(
        "--dir",
        type=str,
        default="/app/curriculum_data",
        help="Directory containing .md DBA files",
    )
    args = parser.parse_args()

    dir_path = Path(args.dir)
    if not dir_path.exists():
        logger.error(f"Directory not found: {dir_path}")
        sys.exit(1)

    md_files = sorted(dir_path.glob("*.md"))
    if not md_files:
        logger.error(f"No .md files found in {dir_path}")
        sys.exit(1)

    logger.info(f"Found {len(md_files)} markdown files to process")

    # Initialize embedding service (loads model once)
    embedding_service = EmbeddingService()

    total_stored = 0
    for md_file in md_files:
        stored = await ingest_file(md_file, embedding_service)
        total_stored += stored

    logger.info(f"\nDone! Total embeddings stored: {total_stored}")


if __name__ == "__main__":
    asyncio.run(main())
