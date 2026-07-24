import type { AxiosError } from 'axios';

interface FieldError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

interface ApiErrorResponse {
  detail: FieldError[] | string;
}

/**
 * Extracts a user-friendly error message from an Axios error.
 * Handles common HTTP status codes with Spanish messages.
 */
export function getApiErrorMessage(error: unknown): string {
  const axiosErr = error as AxiosError<ApiErrorResponse>;

  // Network error (no response received)
  if (axiosErr.code === 'ERR_NETWORK' || !axiosErr.response) {
    return 'Error de conexión. Verifica tu conexión a internet.';
  }

  const status = axiosErr.response.status;

  switch (status) {
    case 401:
      return 'Sesión expirada. Por favor inicia sesión nuevamente.';

    case 422: {
      const detail = axiosErr.response.data?.detail;
      if (Array.isArray(detail)) {
        return detail
          .map((e) => {
            const field = e.loc.length > 1 ? e.loc[e.loc.length - 1] : '';
            return field ? `${field}: ${e.msg}` : e.msg;
          })
          .join('. ');
      }
      if (typeof detail === 'string') {
        return detail;
      }
      return 'Los datos enviados son inválidos. Revisa los campos del formulario.';
    }

    case 504:
      return 'El servicio de IA no respondió a tiempo. Por favor intenta de nuevo.';

    default:
      return 'Ha ocurrido un error inesperado.';
  }
}
