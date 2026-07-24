import type { Classroom, ClassroomCreate, ClassroomUpdate } from '../types/classroom';
import api from './api';

export async function createClassroom(data: ClassroomCreate): Promise<Classroom> {
  const response = await api.post<Classroom>('/classes', data);
  return response.data;
}

export async function getClassrooms(): Promise<Classroom[]> {
  const response = await api.get<Classroom[]>('/classes');
  return response.data;
}

export async function updateClassroom(id: number, data: ClassroomUpdate): Promise<Classroom> {
  const response = await api.put<Classroom>(`/classes/${id}`, data);
  return response.data;
}

export async function deleteClassroom(id: number): Promise<void> {
  await api.delete(`/classes/${id}`);
}
