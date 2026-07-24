import type { ActivityOutput, GenerateRequest } from '../types/activity';
import api from './api';
import {
  mockGenerateActivity,
  mockGetHistory,
  mockGetActivity,
  mockDeleteActivity,
} from '../mocks/mockServices';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export interface HistoryParams {
  subject_id?: number;
  class_id?: number;
  search?: string;
}

export async function generateActivity(data: GenerateRequest): Promise<ActivityOutput> {
  if (USE_MOCKS) return mockGenerateActivity(data);
  const response = await api.post<ActivityOutput>('/activities/generate', data);
  return response.data;
}

export async function getHistory(params?: HistoryParams): Promise<ActivityOutput[]> {
  if (USE_MOCKS) return mockGetHistory(params);
  const response = await api.get<ActivityOutput[]>('/history', { params });
  return response.data;
}

export async function getActivity(id: number): Promise<ActivityOutput> {
  if (USE_MOCKS) return mockGetActivity(id);
  const response = await api.get<ActivityOutput>(`/history/${id}`);
  return response.data;
}

export async function deleteActivity(id: number): Promise<void> {
  if (USE_MOCKS) return mockDeleteActivity(id);
  await api.delete(`/history/${id}`);
}

export async function searchHistory(keyword: string): Promise<ActivityOutput[]> {
  return getHistory({ search: keyword });
}
