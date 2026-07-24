import type { ActivityOutput, GenerateRequest } from '../types/activity';
import api from './api';

export interface HistoryParams {
  subject_id?: number;
  class_id?: number;
  search?: string;
}

export async function generateActivity(data: GenerateRequest): Promise<ActivityOutput> {
  const response = await api.post<ActivityOutput>('/activities/generate', data);
  return response.data;
}

export async function getHistory(params?: HistoryParams): Promise<ActivityOutput[]> {
  const response = await api.get<ActivityOutput[]>('/history', { params });
  return response.data;
}

export async function getActivity(id: number): Promise<ActivityOutput> {
  const response = await api.get<ActivityOutput>(`/history/${id}`);
  return response.data;
}

export async function deleteActivity(id: number): Promise<void> {
  await api.delete(`/history/${id}`);
}

export async function searchHistory(keyword: string): Promise<ActivityOutput[]> {
  return getHistory({ search: keyword });
}
