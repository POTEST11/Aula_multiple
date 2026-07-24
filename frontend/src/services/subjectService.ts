import type { Subject, SubjectCreate } from '../types/subject';
import api from './api';
import { mockGetSubjects, mockCreateSubject, mockDeleteSubject } from '../mocks/mockServices';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export async function createSubject(data: SubjectCreate): Promise<Subject> {
  if (USE_MOCKS) return mockCreateSubject(data);
  const response = await api.post<Subject>('/subjects', data);
  return response.data;
}

export async function getSubjects(): Promise<Subject[]> {
  if (USE_MOCKS) return mockGetSubjects();
  const response = await api.get<Subject[]>('/subjects');
  return response.data;
}

export async function deleteSubject(id: number): Promise<void> {
  if (USE_MOCKS) return mockDeleteSubject(id);
  await api.delete(`/subjects/${id}`);
}
