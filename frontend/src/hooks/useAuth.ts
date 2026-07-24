import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, register } from '../services/authService';
import type { LoginRequest, RegisterRequest } from '../types/auth';
import type { AxiosError } from 'axios';

interface FieldError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

interface ValidationErrorResponse {
  detail: FieldError[] | string;
}

export function useAuth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  function extractErrorMessage(err: unknown): string {
    const axiosErr = err as AxiosError<ValidationErrorResponse>;
    if (axiosErr.response?.data?.detail) {
      const detail = axiosErr.response.data.detail;
      if (Array.isArray(detail)) {
        return detail.map((e) => e.msg).join('. ');
      }
      if (typeof detail === 'string') {
        return detail;
      }
    }
    if (axiosErr.message) {
      return axiosErr.message;
    }
    return 'Ha ocurrido un error inesperado';
  }

  async function handleLogin(data: LoginRequest) {
    setLoading(true);
    setError(null);
    try {
      await login(data);
      navigate('/dashboard/classes');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(data: RegisterRequest) {
    setLoading(true);
    setError(null);
    try {
      await register(data);
      navigate('/dashboard/classes');
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return { loading, error, handleLogin, handleRegister };
}
