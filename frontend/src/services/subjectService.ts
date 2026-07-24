import type { Subject, SubjectCreate } from '../types/subject';
import api from './api';

export async function createSubject(data: SubjectCreate): Promise<Subject> {
  const response = await api.post<Subject>('/subjects', data);
  return response.data;
}

export async function getSubjects(): Promise<Subject[]> {
  const response = await api.get<Subject[]>('/subjects');
  return response.data;
}

export async function deleteSubject(id: number): Promise<void> {
  await api.delete(`/subjects/${id}`);
}
