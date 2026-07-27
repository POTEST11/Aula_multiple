"""Document upload, listing, and deletion endpoints."""

from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.classes import get_class_by_id
from app.dependencies import async_session_factory, get_current_user, get_db
from app.models.class_document import ClassDocument
from app.models.user import User
from app.rag.embeddings import EmbeddingService
from app.schemas.document import DocumentResponse
from app.services.document_processor import DocumentProcessor

router = APIRouter(prefix="/classes/{class_id}/documents", tags=["documents"])


async def verify_classroom_ownership(
    db: AsyncSession, class_id: int, user_id: int
) -> None:
    """Verify that the classroom exists and belongs to the authenticated user.

    Args:
        db: Async database session.
        class_id: The classroom ID to verify.
        user_id: The authenticated user's ID.

    Raises:
        HTTPException: 404 if classroom doesn't exist or user is not the owner.
    """
    classroom = await get_class_by_id(db, class_id=class_id, user_id=user_id)
    if classroom is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clase no encontrada",
        )

# Constants
MAX_FILE_SIZE = 20_971_520  # 20 MB
ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg"}
EXTENSION_MIME_MAP = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
UPLOAD_BASE_DIR = Path("/app/uploads")


_embedding_service: EmbeddingService | None = None


def _get_embedding_service() -> EmbeddingService:
    """Return a module-level cached EmbeddingService instance.

    Avoids reloading the sentence-transformers model on every upload.
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


async def process_document_task(document_id: int) -> None:
    """Background task that processes an uploaded document.

    Creates a DocumentProcessor with the app's session factory and a cached
    EmbeddingService, then runs the full processing pipeline (text extraction,
    chunking, embedding generation, and storage).
    """
    embedding_service = _get_embedding_service()
    processor = DocumentProcessor(
        session_factory=async_session_factory,
        embedding_service=embedding_service,
    )
    await processor.process(document_id)


def _validate_file(content: bytes, content_type: str | None, filename: str | None) -> None:
    """Validate uploaded file: empty → size → MIME → extension match.

    Raises HTTPException with HTTP 422 on validation failure.
    """
    # 1. Check empty file
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo está vacío",
        )

    # 2. Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo excede el tamaño máximo de 10 MB",
        )

    # 3. Check MIME type
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Tipo de archivo no soportado. Formatos válidos: PDF, PNG, JPG, JPEG",
        )

    # 4. Check extension-MIME match
    if filename:
        ext = Path(filename).suffix.lower()
        expected_mime = EXTENSION_MIME_MAP.get(ext)
        if expected_mime is None or expected_mime != content_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"La extensión del archivo ({ext}) no coincide con el tipo de contenido ({content_type})"
                ),
            )


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=DocumentResponse)
async def upload_document(
    class_id: int,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload a document to a classroom.

    Validates file type, size, and extension match. Saves the file to disk,
    creates a ClassDocument record, and enqueues background processing.
    """
    # Verify classroom ownership
    await verify_classroom_ownership(db, class_id=class_id, user_id=current_user.id)

    # Read file content
    content = await file.read()

    # Validate file
    _validate_file(content=content, content_type=file.content_type, filename=file.filename)

    # Generate UUID-based filename
    original_filename = file.filename or "document"
    ext = Path(original_filename).suffix.lower()
    unique_filename = f"{uuid4()}{ext}"

    # Save file to disk
    upload_dir = UPLOAD_BASE_DIR / str(class_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / unique_filename

    file_path.write_bytes(content)

    # Create ClassDocument record
    document = ClassDocument(
        classroom_id=class_id,
        user_id=current_user.id,
        filename=unique_filename,
        original_filename=original_filename,
        file_path=str(file_path),
        mime_type=file.content_type,
        file_size_bytes=len(content),
        status="pending",
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Enqueue background processing task
    background_tasks.add_task(process_document_task, document.id)

    return DocumentResponse.model_validate(document)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentResponse]:
    """List all documents for a classroom, ordered by upload date descending.

    Returns an empty list if no documents exist for the classroom.
    """
    await verify_classroom_ownership(db, class_id=class_id, user_id=current_user.id)

    result = await db.execute(
        select(ClassDocument)
        .where(ClassDocument.classroom_id == class_id)
        .order_by(ClassDocument.uploaded_at.desc())
    )
    documents = result.scalars().all()

    return [DocumentResponse.model_validate(doc) for doc in documents]


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    class_id: int,
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document from a classroom.

    Removes the physical file from disk and deletes the ClassDocument record
    (cascade deletes associated embeddings). Works regardless of document status.
    """
    # Verify classroom ownership
    await verify_classroom_ownership(db, class_id=class_id, user_id=current_user.id)

    # Query document ensuring it belongs to this classroom
    result = await db.execute(
        select(ClassDocument).where(
            ClassDocument.id == document_id,
            ClassDocument.classroom_id == class_id,
        )
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado",
        )

    # Delete physical file from disk (ignore if not found)
    try:
        Path(document.file_path).unlink()
    except FileNotFoundError:
        pass

    # Delete record from database (cascade deletes embeddings)
    await db.delete(document)
    await db.commit()
