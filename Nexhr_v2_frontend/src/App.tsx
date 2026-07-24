import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { AuthLayout } from './components/AuthLayout';
import { GuestOnly, RequireAuth } from './components/RouteGuards';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { OrganizationCreatePage } from './pages/OrganizationCreatePage';
import { RegisterPage } from './pages/RegisterPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { VerifyEmailPage } from './pages/VerifyEmailPage';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/auth/login" replace />} />

          <Route element={<AuthLayout />}>
            <Route element={<GuestOnly />}>
              <Route path="/auth/login" element={<LoginPage />} />
              <Route path="/auth/register" element={<RegisterPage />} />
              <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
            </Route>
            <Route path="/auth/verify-email" element={<VerifyEmailPage />} />

            <Route element={<RequireAuth />}>
              <Route path="/organizations/create" element={<OrganizationCreatePage />} />
            </Route>
          </Route>

          <Route element={<RequireAuth />}>
            <Route path="/app" element={<HomePage />} />
          </Route>

          <Route path="*" element={<Navigate to="/auth/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
