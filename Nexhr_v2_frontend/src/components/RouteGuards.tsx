import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function RequireAuth() {
  const { isAuthenticated, bootstrapping } = useAuth();
  const location = useLocation();

  if (bootstrapping) {
    return <div className="boot-screen">Loading…</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

export function GuestOnly() {
  const { isAuthenticated, bootstrapping, getAccessToken } = useAuth();

  if (bootstrapping) {
    return <div className="boot-screen">Loading…</div>;
  }

  if (isAuthenticated && getAccessToken()) {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}
