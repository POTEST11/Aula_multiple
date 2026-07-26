# Implementation Plan: Class Document Upload

## Overview

Implement document upload functionality for Aula Múltiple classrooms. Teachers upload PDF/image files, the system processes them asynchronously (text extraction → chunking → embedding → pgvector storage), and the agent's curriculum_analysis node queries class-specific embeddings alongside global curriculum when generating activities.

## Tasks

- [x] 1. Database models and migration
  - [x] 1.1 Create ClassDocument and DocumentEmbedding SQLAlchemy models
    - Create `app/models/class_document.py` with the ClassDocument model (id, classroom_id, user_id, filename, original_filename, file_path, mime_type, file_size_bytes, status, error_message, chunk_count, uploaded_at, processed_at)
    - Create `app/models/document_embedding.py` with the DocumentEmbedding model (id, document_id, classroom_id, content, content_hash, chunk_index, embedding Vector(384), created_at)
    - Add UniqueConstraint on (document_id, content_hash) and index on classroom_id
    - Add relationships: ClassDocument.embeddings, Classroom.documents
    - Export models in `app/models/__init__.py`
    - _Requirements: 5.1, 5.3, 10.1, 10.2, 10.4_

  - [x] 1.2 Create Alembic migration for class_documents and document_embeddings tables
    - Generate migration script that creates `class_documents` table with all columns and indexes
    - Creates `document_embeddings` table with pgvector extension and Vector(384) column
    - Adds foreign keys with CASCADE delete
    - Ensures pgvector extension is enabled (`CREATE EXTENSION IF NOT EXISTS vector`)
    - _Requirements: 10.1, 10.2, 10.4_

  - [x] 1.3 Create Pydantic schemas for document API responses
    - Create `app/schemas/document.py` with DocumentResponse and DocumentChunk schemas
    - DocumentResponse includes: id, classroom_id, filename, original_filename, mime_type, file_size_bytes, status, error_message, chunk_count, uploaded_at, processed_at
    - DocumentChunk includes: content, document_filename, similarity_score
    - _Requirements: 1.1, 5.1_

- [x] 2. Document Upload API
  - [x] 2.1 Implement upload endpoint with file validation
    - Create `app/api/documents.py` with router prefix `/classes/{class_id}/documents`
    - Implement `POST ""` endpoint that validates file size (<=10MB), MIME type ({application/pdf, image/png, image/jpeg}), extension-MIME match, and non-empty file
    - Validate size before MIME type per requirement 2.5
    - Save file to `/app/uploads/{classroom_id}/{uuid}.{ext}` using UUID-based naming
    - Create ClassDocument record with status="pending"
    - Enqueue BackgroundTask for document processing
    - Return HTTP 202 with DocumentResponse
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 2.2 Implement ownership verification and classroom access control
    - Add helper function to verify classroom exists and belongs to authenticated user
    - Return HTTP 404 "Clase no encontrada" if classroom doesn't exist or user is not owner
    - Apply ownership check to all document endpoints
    - _Requirements: 8.1, 8.2, 8.4_

  - [x] 2.3 Implement list documents endpoint
    - Implement `GET ""` that returns all ClassDocument records for the classroom
    - Order by uploaded_at descending
    - Apply ownership verification
    - Return empty list if no documents exist
    - _Requirements: 1.3, 8.5_

  - [x] 2.4 Implement delete document endpoint
    - Implement `DELETE "/{document_id}"` that removes ClassDocument record (cascade deletes embeddings)
    - Delete physical file from disk (ignore if file doesn't exist)
    - Allow deletion even if document status is "processing"
    - Return HTTP 204 on success, HTTP 404 if document doesn't exist or doesn't belong to user's classroom
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 2.5 Register document router in the FastAPI application
    - Import and include the documents router in the main app or API router
    - Ensure it's under the `/api/v1` prefix
    - _Requirements: 1.1_

  - [x] 2.6 Write property tests for file validation logic
    - **Property 8: File Type Enforcement** — For any file with MIME type not in {application/pdf, image/png, image/jpeg}, upload is rejected with HTTP 422
    - **Property 9: Size Enforcement** — For any file exceeding 10,485,760 bytes, upload is rejected with HTTP 422
    - **Validates: Requirements 2.1, 2.2, 2.3**

  - [x] 2.7 Write property test for ownership isolation
    - **Property 5: Ownership Isolation** — For any user who does not own a classroom, all upload/list/delete operations on that classroom's documents are rejected with HTTP 404
    - **Validates: Requirements 8.1, 8.2**

- [x] 3. Checkpoint - Ensure models, migration, and API endpoints work
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Document Processing Service
  - [x] 4.1 Implement text extraction functions
    - Create `app/services/document_processor.py` with DocumentProcessor class
    - Implement `extract_text_from_pdf(file_path)` using pdfplumber
    - Implement `extract_text_from_image(file_path)` using pytesseract with Spanish language config
    - Raise ValueError if no text is extracted
    - _Requirements: 3.2, 3.3, 3.8_

  - [x] 4.2 Implement text chunking function
    - Implement `chunk_text(text, chunk_size=500, chunk_overlap=50)` that splits text into overlapping chunks
    - Text shorter than chunk_size results in a single chunk
    - All generated chunks are non-empty strings
    - Adjacent chunks overlap by exactly chunk_overlap characters
    - _Requirements: 3.4_

  - [x] 4.3 Implement the full processing pipeline
    - Implement `async process(document_id)` method
    - Update status to "processing" at start
    - Route to correct extractor based on mime_type
    - Chunk extracted text, generate embeddings via EmbeddingService.generate_batch
    - Compute SHA-256 content_hash for deduplication
    - Store DocumentEmbedding records with classroom_id denormalized
    - On success: set status="ready", chunk_count, processed_at
    - On error: rollback transaction, set status="error", record error_message (max 500 chars)
    - Preserve file on disk regardless of outcome
    - _Requirements: 3.1, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 5.2_

  - [x] 4.4 Write property test for chunking coverage
    - **Property 11: Chunking Coverage** — For any non-empty input text, the concatenation of all chunks (accounting for overlap) reconstructs the original text with no data loss, and every chunk is a non-empty string
    - **Validates: Requirement 3.4**

  - [x] 4.5 Write property test for hash uniqueness
    - **Property 4: Hash Uniqueness per Document** — For any document, no two embeddings within that document share the same content_hash
    - **Validates: Requirement 10.2**

  - [x] 4.6 Write property test for processing completeness
    - **Property 2: Processing Completeness** — For any document with status="ready", document.chunk_count equals the actual count of document_embeddings rows for that document
    - **Validates: Requirements 3.7, 5.3**

  - [x] 4.7 Write property test for transaction atomicity on failure
    - **Property 12: Transaction Atomicity on Failure** — For any document where processing fails at any stage, zero document_embeddings rows exist for that document AND the document status is "error" with a non-empty error_message
    - **Validates: Requirements 4.1, 4.2**

  - [x] 4.8 Write property test for status machine validity
    - **Property 7: Status Machine Validity** — For any document, status transitions follow exactly: pending → processing → ready OR pending → processing → error. No other transitions are permitted
    - **Validates: Requirements 5.1, 5.2**

- [x] 5. Checkpoint - Ensure processing pipeline and property tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Document Retriever
  - [x] 6.1 Implement DocumentRetriever with semantic search
    - Create `app/rag/document_retriever.py` with DocumentRetriever class
    - Implement `async search(query, classroom_id, top_k=5, similarity_threshold=0.65)` method
    - Generate query embedding via EmbeddingService
    - Execute cosine similarity query on document_embeddings filtered by classroom_id
    - Only return chunks from documents with status="ready"
    - Return at most top_k results above threshold, ordered by similarity descending
    - Return empty list if no results meet threshold
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 6.2 Write property test for retrieval correctness
    - **Property 6: Retrieval Correctness** — For any search query with a given classroom_id, all returned results belong to that classroom_id AND have parent document status="ready" AND have similarity_score >= threshold AND are ordered by similarity descending AND result count is at most top_k
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 8.3**

  - [x] 6.3 Write property test for embedding dimensionality
    - **Property 3: Embedding Dimensionality** — For any embedding stored in document_embeddings, the vector has exactly 384 dimensions
    - **Validates: Requirements 3.5, 10.1**

- [x] 7. Enhanced Curriculum Analysis Node
  - [x] 7.1 Extend curriculum_analysis node to query class-specific documents
    - Modify `app/agent/nodes/curriculum_analysis.py` to accept classroom_id from agent state
    - Add DocumentRetriever query alongside existing CurriculumRetriever query
    - Merge both result sets into agent state (curriculum_standards + document_context)
    - If classroom_id is absent, maintain existing behavior (global curriculum only)
    - Document retrieval failure is non-fatal: log warning and continue with empty document_context
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 7.2 Update AgentState type definition to include classroom_id and document_context
    - Add `classroom_id: Optional[int]` to AgentState
    - Add `document_context: list[DocumentChunk]` to AgentState
    - Update downstream nodes that consume state to handle new fields
    - _Requirements: 7.1_

  - [x] 7.3 Write property test for agent resilience
    - **Property 13: Agent Resilience** — For any execution of the Curriculum_Analysis_Node where document retrieval raises an exception, the node still returns valid curriculum_standards results and an empty document_context list
    - **Validates: Requirement 7.2**

- [x] 8. Infrastructure and Dependencies
  - [x] 8.1 Update Dockerfile and docker-compose for Tesseract and uploads volume
    - Add `tesseract-ocr` and `tesseract-ocr-spa` to Dockerfile apt-get install
    - Add `RUN mkdir -p /app/uploads` to Dockerfile
    - Add `uploads` volume to docker-compose.yml backend service
    - _Requirements: 3.3_

  - [x] 8.2 Update requirements.txt with new Python dependencies
    - Add `pytesseract>=0.3.10,<1.0.0`
    - Add `Pillow>=10.0.0,<11.0.0`
    - Add `python-multipart>=0.0.6,<1.0.0` (if not already present)
    - _Requirements: 3.2, 3.3_

- [x] 9. Integration wiring and final validation
  - [x] 9.1 Wire document processing into upload endpoint background task
    - Ensure upload_document endpoint creates DocumentProcessor instance with correct session_factory and EmbeddingService
    - Schedule `process_document(document_id)` as background task
    - Verify the full flow: upload → background processing → embeddings stored
    - _Requirements: 1.2, 3.1_

  - [x] 9.2 Write property test for upload integrity
    - **Property 1: Upload Integrity** — For any valid file upload that returns HTTP 202, a file exists on disk at the stored path AND a row exists in class_documents with status="pending" and correct metadata
    - **Validates: Requirements 1.1**

  - [x] 9.3 Write property test for cascade deletion
    - **Property 10: Cascade Deletion** — For any deleted document, zero document_embeddings rows exist for that document_id AND the physical file no longer exists on disk AND the class_documents row is removed
    - **Validates: Requirements 9.1, 9.2, 9.3**

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document using hypothesis
- Unit tests validate specific examples and edge cases
- The project uses Python with FastAPI, SQLAlchemy (async), pgvector, pdfplumber, pytesseract, and hypothesis for property-based testing
- All background processing uses FastAPI BackgroundTasks (not Celery)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.3", "8.1", "8.2"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1", "2.2"] },
    { "id": 3, "tasks": ["2.3", "2.4", "2.5"] },
    { "id": 4, "tasks": ["2.6", "2.7"] },
    { "id": 5, "tasks": ["4.1", "4.2"] },
    { "id": 6, "tasks": ["4.3"] },
    { "id": 7, "tasks": ["4.4", "4.5", "4.6", "4.7", "4.8"] },
    { "id": 8, "tasks": ["6.1"] },
    { "id": 9, "tasks": ["6.2", "6.3", "7.1", "7.2"] },
    { "id": 10, "tasks": ["7.3", "9.1"] },
    { "id": 11, "tasks": ["9.2", "9.3"] }
  ]
}
```
