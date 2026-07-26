import api from './api';

export interface ClassDocument {
  id: number;
  classroom_id: number;
  filename: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  status: 'pending' | 'processing' | 'ready' | 'error';
  error_message: string | null;
  chunk_count: number | null;
  uploaded_at: string;
  processed_at: string | null;
}

export async function uploadDocument(classId: number, file: File): Promise<ClassDocument> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<ClassDocument>(
    `/classes/${classId}/documents`,
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } }
  );
  return response.data;
}

export async function getDocuments(classId: number): Promise<ClassDocument[]> {
  const response = await api.get<ClassDocument[]>(`/classes/${classId}/documents`);
  return response.data;
}

export async function deleteDocument(classId: number, documentId: number): Promise<void> {
  await api.delete(`/classes/${classId}/documents/${documentId}`);
}
