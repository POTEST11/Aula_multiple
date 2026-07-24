import { Navigate, Outlet } from 'react-router-dom';
import { TOKEN_KEY } from '../../services/api';

export default function ProtectedRoute() {
  // TODO: Remove DEV_BYPASS before production
  const DEV_BYPASS = true;
  if (DEV_BYPASS) return <Outlet />;

  const token = localStorage.getItem(TOKEN_KEY);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
