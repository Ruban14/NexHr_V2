import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { AppShell } from './components/AppShell';
import { AuthLayout } from './components/AuthLayout';
import { GuestOnly, RequireAuth } from './components/RouteGuards';
import { ForgotPasswordPage } from './pages/forgot-password/ForgotPasswordPage';
import { HomePage } from './pages/home/HomePage';
import { LoginPage } from './pages/login/LoginPage';
import { OrganizationCreatePage } from './pages/organization-create/OrganizationCreatePage';
import { OrganizationEditPage } from './pages/organization-edit/OrganizationEditPage';
import { ProfileEditPage } from './pages/profile-edit/ProfileEditPage';
import { RegisterPage } from './pages/register/RegisterPage';
import { ResetPasswordPage } from './pages/reset-password/ResetPasswordPage';
import { SettingsPage } from './pages/settings/SettingsPage';
import { VerifyEmailPage } from './pages/verify-email/VerifyEmailPage';
import { WorkspaceProvider } from './workspace/WorkspaceContext';

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
            <Route
              path="/app"
              element={
                <WorkspaceProvider>
                  <AppShell />
                </WorkspaceProvider>
              }
            >
              <Route index element={<HomePage />} />
              <Route path="organization" element={<OrganizationEditPage />} />
              <Route path="profile" element={<ProfileEditPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/auth/login" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
