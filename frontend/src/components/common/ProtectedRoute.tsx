import { Navigate, Outlet } from 'react-router-dom';
import { TOKEN_KEY } from '../../services/api';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

export default function ProtectedRoute() {
  // In mock mode, bypass auth check so dashboard is always accessible
  if (USE_MOCKS) return <Outlet />;

  const token = localStorage.getItem(TOKEN_KEY);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
