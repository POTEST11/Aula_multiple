"""
Script de ingesta offline para documentos curriculares.

CLI independiente que procesa PDFs curriculares, genera embeddings y los
almacena en pgvector. No requiere que el servidor FastAPI esté corriendo.

Uso:
    python -m scripts.ingest_curriculum --pdf path/al/documento.pdf \
        --country "Colombia" --grade 5 --subject "Matemáticas"

Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import argparse
import asyncio
import hashlib
import logging
import sys
from pathlib import Path

import pdfplumber
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.models.curriculum_embedding import CurriculumEmbedding
from app.rag.embeddings import EmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extrae todo el texto de un archivo PDF usando pdfplumber.

    Args:
        pdf_path: Ruta al archivo PDF.

    Returns:
        Texto completo extraído del PDF.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si no se pudo extraer texto del PDF.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {pdf_path}")

    pages_text: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    full_text = "\n".join(pages_text)
    if not full_text.strip():
        raise ValueError(f"No se pudo extraer texto del PDF: {pdf_path}")

    return full_text


def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    Divide el texto en fragmentos (chunks) con overlap.

    Args:
        text: Texto completo a dividir.
        chunk_size: Tamaño máximo de cada chunk en caracteres.
        chunk_overlap: Número de caracteres de solapamiento entre chunks consecutivos.

    Returns:
        Lista de fragmentos de texto.
    """
    if not text or not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        # Only add non-empty chunks
        if chunk.strip():
            chunks.append(chunk)

        # Move start forward by (chunk_size - overlap)
        start += chunk_size - chunk_overlap

    return chunks


def compute_content_hash(content: str) -> str:
    """
    Calcula el hash SHA-256 del contenido para deduplicación.

    Args:
        content: Texto del fragmento.

    Returns:
        Hash SHA-256 como string hexadecimal de 64 caracteres.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def filter_existing_hashes(
    session: AsyncSession, hashes: list[str]
) -> set[str]:
    """
    Consulta la base de datos para identificar hashes que ya existen.

    Args:
        session: Sesión async de SQLAlchemy.
        hashes: Lista de content_hash a verificar.

    Returns:
        Conjunto de hashes que ya existen en la base de datos.
    """
    if not hashes:
        return set()

    result = await session.execute(
        select(CurriculumEmbedding.content_hash).where(
            CurriculumEmbedding.content_hash.in_(hashes)
        )
    )
    return {row[0] for row in result.fetchall()}


async def ingest_document(
    pdf_path: Path,
    country: str,
    grade: int,
    subject: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> int:
    """
    Procesa un PDF curricular y almacena embeddings en pgvector.

    Proceso:
    1. Extrae texto del PDF (pdfplumber)
    2. Divide en chunks con overlap
    3. Genera embeddings localmente por chunk (batch, sentence-transformers)
    4. Verifica duplicados por hash del contenido
    5. Inserta en tabla curriculum_embeddings

    Args:
        pdf_path: Ruta al archivo PDF.
        country: País del currículo.
        grade: Grado escolar.
        subject: Materia.
        chunk_size: Tamaño de cada chunk en caracteres.
        chunk_overlap: Solapamiento entre chunks consecutivos.

    Returns:
        Número de chunks procesados y almacenados (nuevos, no duplicados).
    """
    settings = get_settings()

    # 1. Extraer texto del PDF
    logger.info("Extrayendo texto de: %s", pdf_path)
    full_text = extract_text_from_pdf(pdf_path)
    logger.info("Texto extraído: %d caracteres", len(full_text))

    # 2. Dividir en chunks
    chunks = chunk_text(full_text, chunk_size, chunk_overlap)
    logger.info("Texto dividido en %d chunks (size=%d, overlap=%d)", len(chunks), chunk_size, chunk_overlap)

    if not chunks:
        logger.warning("No se generaron chunks del documento.")
        return 0

    # 3. Calcular hashes para deduplicación
    chunk_hashes = [compute_content_hash(chunk) for chunk in chunks]

    # 4. Configurar conexión a BD (independiente del servidor)
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # 5. Filtrar chunks ya existentes (deduplicación)
        existing_hashes = await filter_existing_hashes(session, chunk_hashes)
        logger.info("Chunks ya existentes en BD: %d", len(existing_hashes))

        # Filtrar solo chunks nuevos
        new_indices = [
            i for i, h in enumerate(chunk_hashes) if h not in existing_hashes
        ]

        if not new_indices:
            logger.info("Todos los chunks ya estaban ingresados. Nada que hacer.")
            await engine.dispose()
            return 0

        new_chunks = [chunks[i] for i in new_indices]
        new_hashes = [chunk_hashes[i] for i in new_indices]
        logger.info("Chunks nuevos a procesar: %d", len(new_chunks))

        # 6. Generar embeddings en batch
        logger.info("Generando embeddings (batch) con sentence-transformers...")
        embedding_service = EmbeddingService()
        embeddings = await embedding_service.generate_batch(new_chunks)
        logger.info("Embeddings generados: %d vectores de %d dimensiones", len(embeddings), len(embeddings[0]))

        # 7. Insertar en la base de datos
        records = []
        for i, (chunk, content_hash, embedding) in enumerate(
            zip(new_chunks, new_hashes, embeddings)
        ):
            record = CurriculumEmbedding(
                country=country,
                grade=grade,
                subject=subject,
                content=chunk,
                content_hash=content_hash,
                embedding=embedding,
                extra_metadata={
                    "source_file": pdf_path.name,
                    "chunk_index": new_indices[i],
                    "total_chunks": len(chunks),
                },
            )
            records.append(record)

        session.add_all(records)
        await session.commit()
        logger.info("Insertados %d registros en curriculum_embeddings.", len(records))

    await engine.dispose()
    return len(records)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """
    Parsea argumentos de línea de comandos.

    Args:
        args: Lista de argumentos (None usa sys.argv).

    Returns:
        Namespace con los argumentos parseados.
    """
    parser = argparse.ArgumentParser(
        description="Ingesta offline de documentos curriculares a pgvector.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplo de uso:
    python -m scripts.ingest_curriculum --pdf curriculo_colombia_5.pdf \\
        --country "Colombia" --grade 5 --subject "Matemáticas"
        """,
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        required=True,
        help="Ruta al archivo PDF curricular a procesar.",
    )
    parser.add_argument(
        "--country",
        type=str,
        required=True,
        help="País del currículo (ej: Colombia, México, Argentina).",
    )
    parser.add_argument(
        "--grade",
        type=int,
        required=True,
        help="Grado escolar (número entero, ej: 5).",
    )
    parser.add_argument(
        "--subject",
        type=str,
        required=True,
        help="Materia del currículo (ej: Matemáticas, Ciencias).",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=500,
        help="Tamaño de cada chunk en caracteres (default: 500).",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=50,
        help="Solapamiento entre chunks en caracteres (default: 50).",
    )
    return parser.parse_args(args)


async def main() -> None:
    """Punto de entrada principal del script CLI."""
    args = parse_args()

    if not args.pdf.exists():
        logger.error("El archivo PDF no existe: %s", args.pdf)
        sys.exit(1)

    if not str(args.pdf).lower().endswith(".pdf"):
        logger.error("El archivo debe ser un PDF: %s", args.pdf)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("INGESTA DE DOCUMENTO CURRICULAR")
    logger.info("=" * 60)
    logger.info("PDF: %s", args.pdf)
    logger.info("País: %s", args.country)
    logger.info("Grado: %d", args.grade)
    logger.info("Materia: %s", args.subject)
    logger.info("Chunk size: %d | Overlap: %d", args.chunk_size, args.chunk_overlap)
    logger.info("-" * 60)

    try:
        inserted = await ingest_document(
            pdf_path=args.pdf,
            country=args.country,
            grade=args.grade,
            subject=args.subject,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
        )
        logger.info("-" * 60)
        logger.info("RESULTADO: %d chunks nuevos insertados.", inserted)
        logger.info("=" * 60)
    except Exception as e:
        logger.error("Error durante la ingesta: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
