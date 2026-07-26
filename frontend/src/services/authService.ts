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
  // Register creates the user, then login to get a token
  await api.post('/auth/register', data);
  // Auto-login after successful registration
  const loginResponse = await api.post<TokenResponse>('/auth/login', {
    email: data.email,
    password: data.password,
  });
  localStorage.setItem(TOKEN_KEY, loginResponse.data.access_token);
  return loginResponse.data;
}

export function logout(): void {
  localStorage.removeItem(TOKEN_KEY);
}
