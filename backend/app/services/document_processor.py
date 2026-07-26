"""Document processing service for text extraction, chunking, and embedding generation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import func

from app.models.class_document import ClassDocument
from app.models.document_embedding import DocumentEmbedding

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.rag.embeddings import EmbeddingService


class DocumentProcessor:
    """Orchestrates background pipeline: text extraction → chunking → embedding → storage."""

    def __init__(
        self,
        session_factory: async_sessionmaker,
        embedding_service: EmbeddingService,
    ) -> None:
        self.session_factory = session_factory
        self.embedding_service = embedding_service

    def extract_text_from_pdf(self, file_path: Path) -> str:
        """Extract text from a PDF file using pdfplumber.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text as a string.

        Raises:
            ValueError: If no text could be extracted.
        """
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        full_text = "\n".join(text_parts)
        if not full_text.strip():
            raise ValueError("No se pudo extraer texto del documento")
        return full_text

    def extract_text_from_image(self, file_path: Path) -> str:
        """Extract text from an image file using Tesseract OCR.

        Args:
            file_path: Path to the image file (PNG, JPG, JPEG).

        Returns:
            OCR-extracted text as a string.

        Raises:
            ValueError: If no text could be extracted.
        """
        import pytesseract
        from PIL import Image

        image = Image.open(file_path)
        text = pytesseract.image_to_string(image, lang="spa")

        if not text.strip():
            raise ValueError("No se pudo extraer texto del documento")
        return text

    def chunk_text(
        self, text: str, chunk_size: int = 500, chunk_overlap: int = 50
    ) -> list[str]:
        """Split text into overlapping chunks.

        Algorithm:
        - If text length <= chunk_size, return [text] as single chunk
        - Otherwise, create chunks of chunk_size characters
        - Each new chunk starts at step = chunk_size - chunk_overlap from the previous
        - Adjacent chunks overlap by exactly chunk_overlap characters
        - All chunks are non-empty strings
        - The last chunk may be shorter than chunk_size but must be non-empty

        The property to maintain: concatenating chunks (removing overlap)
        reconstructs the original text with no data loss.

        Args:
            text: The input text to chunk.
            chunk_size: Maximum size of each chunk in characters.
            chunk_overlap: Number of characters that overlap between adjacent chunks.

        Returns:
            A list of non-empty string chunks covering the entire input text.
        """
        if not text:
            return []

        if len(text) <= chunk_size:
            return [text]

        step = chunk_size - chunk_overlap
        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            # If this chunk reached (or passed) the end of text, we're done
            if end >= len(text):
                break
            start += step

        return chunks

    async def process(self, document_id: int) -> None:
        """Full background processing pipeline for an uploaded document.

        Pipeline steps:
        1. Load document record, verify status is "pending", update to "processing"
        2. Extract text based on MIME type (PDF via pdfplumber, images via Tesseract OCR)
        3. Chunk extracted text into overlapping segments
        4. Generate embeddings in batch via EmbeddingService
        5. Compute SHA-256 content_hash for deduplication
        6. Store DocumentEmbedding records with classroom_id denormalized
        7. On success: set status="ready", chunk_count, processed_at
        8. On error: rollback transaction, set status="error", record error_message

        The file on disk is preserved regardless of outcome.

        Args:
            document_id: Primary key of the ClassDocument to process.
        """
        async with self.session_factory() as session:
            # Step 1: Load document and validate status
            document = await session.get(ClassDocument, document_id)
            if document is None or document.status != "pending":
                return

            # Transition: pending → processing
            document.status = "processing"
            await session.commit()

            try:
                # Step 2: Extract text based on MIME type
                file_path = Path(document.file_path)
                if document.mime_type == "application/pdf":
                    extracted_text = self.extract_text_from_pdf(file_path)
                else:  # image/png or image/jpeg
                    extracted_text = self.extract_text_from_image(file_path)

                if not extracted_text.strip():
                    raise ValueError("No se pudo extraer texto del documento")

                # Step 3: Chunk text
                chunks = self.chunk_text(
                    extracted_text, chunk_size=500, chunk_overlap=50
                )

                # Step 4: Generate embeddings in batch
                embeddings = await self.embedding_service.generate_batch(chunks)

                # Step 5: Compute SHA-256 hashes for deduplication
                chunk_hashes = [
                    hashlib.sha256(c.encode()).hexdigest() for c in chunks
                ]

                # Step 6: Store embedding records (deduplicated by content_hash)
                records = []
                seen_hashes: set[str] = set()
                for idx, (chunk, chunk_hash, embedding) in enumerate(
                    zip(chunks, chunk_hashes, embeddings)
                ):
                    if chunk_hash in seen_hashes:
                        continue
                    seen_hashes.add(chunk_hash)
                    records.append(
                        DocumentEmbedding(
                            document_id=document.id,
                            classroom_id=document.classroom_id,
                            content=chunk,
                            content_hash=chunk_hash,
                            chunk_index=idx,
                            embedding=embedding,
                        )
                    )
                session.add_all(records)

                # Step 7: Mark as ready
                document.status = "ready"
                document.chunk_count = len(records)
                document.processed_at = func.now()
                await session.commit()

            except Exception as exc:
                await session.rollback()
                # Re-fetch document in a new transaction to update error status
                async with self.session_factory() as error_session:
                    document = await error_session.get(
                        ClassDocument, document_id
                    )
                    if document:
                        document.status = "error"
                        document.error_message = str(exc)[:500]
                        await error_session.commit()
