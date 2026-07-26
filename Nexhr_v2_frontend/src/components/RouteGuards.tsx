import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function RequireAuth() {
  const { isAuthenticated, bootstrapping, user } = useAuth();
  const location = useLocation();

  if (bootstrapping) {
    return <div className="boot-screen">Loading…</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace state={{ from: location.pathname }} />;
  }

  const onChangePassword = location.pathname === '/auth/change-password';
  if (user?.must_change_password && !onChangePassword) {
    return <Navigate to="/auth/change-password" replace />;
  }

  if (!user?.must_change_password && onChangePassword) {
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}

export function GuestOnly() {
  const { isAuthenticated, bootstrapping, getAccessToken, user } = useAuth();

  if (bootstrapping) {
    return <div className="boot-screen">Loading…</div>;
  }

  if (isAuthenticated && getAccessToken()) {
    if (user?.must_change_password) {
      return <Navigate to="/auth/change-password" replace />;
    }
    return <Navigate to="/app" replace />;
  }

  return <Outlet />;
}
