# Requirements Document

## Introduction

This document specifies the requirements for the Class Document Upload feature in Aula Múltiple. The feature allows teachers to upload PDF and image files (PNG, JPG, JPEG) associated to a specific classroom. The system processes uploads asynchronously — extracting text, chunking, generating embeddings, and storing vectors — so that the agent's curriculum analysis node can query class-specific documents alongside global curriculum standards when generating activities.

## Glossary

- **Upload_API**: The set of REST endpoints under `/api/v1/classes/{class_id}/documents` that handle document upload, listing, and deletion
- **Document_Processor**: The background service that orchestrates text extraction, chunking, embedding generation, and storage for an uploaded document
- **Document_Retriever**: The service that performs semantic similarity search over class-specific document embeddings
- **Curriculum_Analysis_Node**: The agent pipeline node that queries both global curriculum embeddings and class-specific document embeddings to provide context for activity generation
- **Class_Document**: A database record representing an uploaded file associated to a classroom, including its processing status
- **Document_Embedding**: A vectorized text chunk stored in pgvector, derived from a class document
- **Status_Machine**: The document lifecycle states: `pending` → `processing` → `ready` | `error`
- **Embedding_Service**: The existing sentence-transformers service that generates 384-dimensional vector embeddings from text
- **Classroom_Owner**: The authenticated user who created and owns a specific classroom

## Requirements

### Requirement 1: Document Upload

**User Story:** As a teacher, I want to upload PDF and image files to my classroom, so that the system can use my teaching materials as context for generating activities.

#### Acceptance Criteria

1. WHEN a Classroom_Owner submits a valid file via multipart/form-data to the Upload_API, THE Upload_API SHALL save the file to disk under `/app/uploads/{classroom_id}/{uuid}.{ext}`, create a Class_Document record with status "pending", and return HTTP 202 with a JSON response containing the document id, filename, original_filename, mime_type, file_size_bytes, status, uploaded_at, and null fields for chunk_count and processed_at
2. WHEN a file is uploaded successfully, THE Upload_API SHALL enqueue a background processing task for the Document_Processor without blocking the HTTP response, ensuring the endpoint returns within 1 second regardless of file size
3. WHEN a Classroom_Owner requests the document list for a classroom, THE Upload_API SHALL return all Class_Document records belonging to that classroom ordered by uploaded_at descending

### Requirement 2: File Validation

**User Story:** As a teacher, I want the system to validate my uploaded files, so that only supported formats within size limits are accepted.

#### Acceptance Criteria

1. WHEN an uploaded file has a MIME type not in the set {application/pdf, image/png, image/jpeg}, THE Upload_API SHALL reject the request with HTTP 422 and message "Tipo de archivo no soportado. Formatos válidos: PDF, PNG, JPG, JPEG"
2. WHEN an uploaded file exceeds 10,485,760 bytes (10 MB), THE Upload_API SHALL reject the request with HTTP 422 and message "El archivo excede el tamaño máximo de 10 MB"
3. WHEN the Upload_API receives a file whose extension does not match its MIME type header (e.g., a .png extension with application/pdf MIME type), THE Upload_API SHALL reject the request with HTTP 422 and a message indicating format mismatch between extension and content type
4. WHEN an uploaded file has a size of 0 bytes, THE Upload_API SHALL reject the request with HTTP 422 and a message indicating that the file is empty
5. THE Upload_API SHALL validate file size before MIME type and extension checks, rejecting oversized files without further processing

### Requirement 3: Background Document Processing

**User Story:** As a teacher, I want my uploaded documents processed automatically in the background, so that I can continue working while the system extracts and indexes the content.

#### Acceptance Criteria

1. WHEN the Document_Processor begins processing a document, THE Document_Processor SHALL update the document status from "pending" to "processing"
2. WHEN a PDF file is processed, THE Document_Processor SHALL extract text using pdfplumber
3. WHEN an image file (PNG, JPG, JPEG) is processed, THE Document_Processor SHALL extract text using Tesseract OCR
4. WHEN text extraction produces at least 1 non-whitespace character, THE Document_Processor SHALL split the text into chunks of 500 characters with 50 characters of overlap, where text shorter than 500 characters results in a single chunk
5. WHEN chunks are generated, THE Document_Processor SHALL generate 384-dimensional embeddings for each chunk via the Embedding_Service
6. WHEN embeddings are generated, THE Document_Processor SHALL store each embedding in the document_embeddings table with content, content_hash (SHA-256), a zero-based sequential chunk_index, and classroom_id, skipping any chunk whose content_hash already exists for the same document
7. WHEN processing completes successfully, THE Document_Processor SHALL update the document status to "ready", set chunk_count to the number of chunks stored, and set processed_at to the current timestamp
8. IF text extraction produces zero non-whitespace characters, THEN THE Document_Processor SHALL set the document status to "error" and record an error_message indicating that no extractable text was found

### Requirement 4: Processing Error Handling

**User Story:** As a teacher, I want to know when document processing fails, so that I can take corrective action such as re-uploading a clearer file.

#### Acceptance Criteria

1. IF text extraction fails (corrupted file, blank image, no OCR text), THEN THE Document_Processor SHALL set the document status to "error" and record an error_message that indicates the failure category (corrupted file, blank content, or OCR extraction failure) in at most 500 characters
2. IF any exception occurs during processing, THEN THE Document_Processor SHALL roll back the transaction so that no partial embeddings are stored
3. IF processing fails, THEN THE Document_Processor SHALL preserve the original file on disk until manually removed
4. WHEN the Document_Processor sets a document status to "error", THE Document_Processor SHALL make the error status and error_message retrievable by the teacher through the document listing endpoint

### Requirement 5: Document Status State Machine

**User Story:** As a teacher, I want to see the processing status of my documents, so that I know when they are ready for use by the agent.

#### Acceptance Criteria

1. THE Status_Machine SHALL restrict document status values to: "pending", "processing", "ready", "error"
2. THE Status_Machine SHALL only allow the transitions: pending → processing, processing → ready, processing → error
3. WHEN a document is first registered in the system, THE Status_Machine SHALL assign the initial status "pending"
4. IF a status transition is attempted that is not in the allowed set (pending → processing, processing → ready, processing → error), THEN THE Status_Machine SHALL reject the transition and preserve the current status unchanged
5. IF a document has status "ready", THEN THE Class_Document SHALL have a non-null chunk_count with a value greater than or equal to 1, equal to the number of Document_Embedding records associated with the document
6. IF a document transitions to status "error", THEN THE Class_Document SHALL store an error reason describing the failure that occurred during processing

### Requirement 6: Document Retrieval (Semantic Search)

**User Story:** As the agent system, I want to search class-specific document embeddings by semantic similarity, so that relevant document context is available during activity generation.

#### Acceptance Criteria

1. WHEN the Document_Retriever receives a non-empty query (1 to 500 characters) and a valid classroom_id, THE Document_Retriever SHALL generate a query embedding using the Embedding_Service and execute a cosine similarity search against the document_embeddings table filtered to that classroom_id
2. THE Document_Retriever SHALL return at most top_k results (default 5, minimum 1, maximum 20), where each result includes the chunk text content, the source document filename, and the similarity score, ordered by similarity score descending
3. THE Document_Retriever SHALL exclude results with similarity score below the threshold (default 0.65, valid range above 0.0 up to 1.0 inclusive)
4. THE Document_Retriever SHALL only return chunks from documents with status "ready"
5. WHEN no documents exist for the classroom or no results meet the threshold, THE Document_Retriever SHALL return an empty list
6. IF the Embedding_Service fails to generate the query embedding, THEN THE Document_Retriever SHALL raise an error without returning partial results

### Requirement 7: Enhanced Curriculum Analysis

**User Story:** As a teacher, I want the agent to consider my uploaded classroom documents alongside the global curriculum when generating activities, so that activities are grounded in my specific teaching materials.

#### Acceptance Criteria

1. WHEN a classroom_id is present in the agent state, THE Curriculum_Analysis_Node SHALL query global curriculum embeddings (up to 5 results) and class-specific document embeddings associated with that classroom_id (up to 5 results), and merge both result sets into the agent state
2. IF the class-specific document retrieval fails, THEN THE Curriculum_Analysis_Node SHALL log the error including the classroom_id and continue using only the global curriculum results without interrupting the generation pipeline
3. WHEN no classroom_id is present in the agent state, THE Curriculum_Analysis_Node SHALL query only global curriculum embeddings returning up to 5 results (existing behavior unchanged)
4. IF both global curriculum retrieval and class-specific document retrieval return no results above the configured similarity threshold, THEN THE Curriculum_Analysis_Node SHALL proceed with an empty curriculum_standards list and set the current_node to "curriculum_analysis"

### Requirement 8: Ownership Isolation

**User Story:** As a teacher, I want my classroom documents to be private to my classroom, so that other users cannot access my teaching materials.

#### Acceptance Criteria

1. WHEN a user attempts to upload, list, or delete documents for a classroom, THE Upload_API SHALL verify that the authenticated user's ID matches the owner_id of the target classroom before executing the operation
2. IF the specified classroom_id does not exist in the database or the classroom's owner_id does not match the authenticated user's ID, THEN THE Upload_API SHALL respond with HTTP 404 "Clase no encontrada" without revealing whether the classroom exists for another user
3. THE Document_Retriever SHALL include the classroom_id as a mandatory filter in every database query, ensuring that no query can return documents belonging to a different classroom_id than the one specified in the request
4. IF a user submits a request with a classroom_id parameter that is missing or not a valid positive integer, THEN THE Upload_API SHALL respond with HTTP 422 indicating the invalid field
5. WHEN the Upload_API returns a list of documents for a classroom, THE Upload_API SHALL return only documents whose classroom_id matches the requested classroom and whose classroom owner_id matches the authenticated user, returning an empty list if no documents exist

### Requirement 9: Document Deletion

**User Story:** As a teacher, I want to delete documents from my classroom, so that outdated or incorrect materials are removed from the system.

#### Acceptance Criteria

1. WHEN a Classroom_Owner deletes a document, THE Upload_API SHALL remove the Class_Document record from the database and cascade-delete all associated Document_Embedding records within a single transaction
2. WHEN a document is deleted from the database, THE Upload_API SHALL remove the physical file from disk
3. IF the physical file does not exist on disk at deletion time, THEN THE Upload_API SHALL proceed with the database deletion without returning an error
4. WHEN a document is successfully deleted, THE Upload_API SHALL return HTTP 204 with no content
5. IF the specified document does not exist or does not belong to the authenticated user's classroom, THEN THE Upload_API SHALL respond with HTTP 404
6. IF the document has status "processing", THEN THE Upload_API SHALL still delete the document, its embeddings, and the file

### Requirement 10: Embedding Integrity

**User Story:** As the system, I want document embeddings to maintain structural integrity, so that retrieval produces correct and consistent results.

#### Acceptance Criteria

1. THE Document_Embedding SHALL store a 384-dimensional vector produced by the all-MiniLM-L6-v2 model, and reject any embedding whose dimension count is not exactly 384
2. THE Document_Embedding SHALL enforce a unique constraint on (document_id, content_hash) using SHA-256 of the chunk text, preventing storage of duplicate chunks within the same document
3. IF an insertion is attempted with a content_hash that already exists for the same document, THEN THE system SHALL skip the duplicate record without raising an error and without modifying the existing record
4. THE Document_Embedding SHALL store classroom_id denormalized from the parent document, and this value SHALL be a non-null foreign key reference used to filter embeddings during similarity queries
