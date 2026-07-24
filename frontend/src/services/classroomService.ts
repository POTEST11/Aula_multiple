import type { Classroom, ClassroomCreate, ClassroomUpdate } from '../types/classroom';
import api from './api';
import {
  mockGetClassrooms,
  mockCreateClassroom,
  mockUpdateClassroom,
  mockDeleteClassroom,
} from '../mocks/mockServices';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export async function createClassroom(data: ClassroomCreate): Promise<Classroom> {
  if (USE_MOCKS) return mockCreateClassroom(data);
  const response = await api.post<Classroom>('/classes', data);
  return response.data;
}

export async function getClassrooms(): Promise<Classroom[]> {
  if (USE_MOCKS) return mockGetClassrooms();
  const response = await api.get<Classroom[]>('/classes');
  return response.data;
}

export async function updateClassroom(id: number, data: ClassroomUpdate): Promise<Classroom> {
  if (USE_MOCKS) return mockUpdateClassroom(id, data);
  const response = await api.put<Classroom>(`/classes/${id}`, data);
  return response.data;
}

export async function deleteClassroom(id: number): Promise<void> {
  if (USE_MOCKS) return mockDeleteClassroom(id);
  await api.delete(`/classes/${id}`);
}
