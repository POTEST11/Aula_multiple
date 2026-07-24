import type { LoginRequest, RegisterRequest, TokenResponse } from '../types/auth';
import api, { TOKEN_KEY } from './api';
import { mockLogin, mockRegister } from '../mocks/mockServices';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export async function login(data: LoginRequest): Promise<TokenResponse> {
  if (USE_MOCKS) return mockLogin();
  const response = await api.post<TokenResponse>('/auth/login', data);
  localStorage.setItem(TOKEN_KEY, response.data.access_token);
  return response.data;
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  if (USE_MOCKS) return mockRegister();
  const response = await api.post<TokenResponse>('/auth/register', data);
  localStorage.setItem(TOKEN_KEY, response.data.access_token);
  return response.data;
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
}
