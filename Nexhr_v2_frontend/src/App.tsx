import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { AppShell } from './components/AppShell';
import { AuthLayout } from './components/AuthLayout';
import { GuestOnly, RequireAuth } from './components/RouteGuards';
import { ForgotPasswordPage } from './pages/forgot-password/ForgotPasswordPage';
import { HomePage } from './pages/home/HomePage';
import { LoginPage } from './pages/login/LoginPage';
import { ChangePasswordPage } from './pages/change-password/ChangePasswordPage';
import { OrganizationCreatePage } from './pages/organization-create/OrganizationCreatePage';
import { OrganizationEditPage } from './pages/organization-edit/OrganizationEditPage';
import { EmployeesPage } from './pages/employees/EmployeesPage';
import { EmployeeDetailPage } from './pages/employees/EmployeeDetailPage';
import { DesignationsPage } from './pages/organization-setup/DesignationsPage';
import { DocumentPoliciesPage } from './pages/organization-setup/DocumentPoliciesPage';
import { DocumentPolicyBuilderPage } from './pages/organization-setup/DocumentPolicyBuilderPage';
import { DocumentsPage } from './pages/organization-setup/DocumentsPage';
import { AssetsPage } from './pages/organization-setup/AssetsPage';
import { LeaveApprovalsPage } from './pages/leave-approvals/LeaveApprovalsPage';
import { AttendancePage } from './pages/attendance/AttendancePage';
import { AttendanceApprovalsPage } from './pages/attendance/AttendanceApprovalsPage';
import { LeavePoliciesPage } from './pages/organization-setup/LeavePoliciesPage';
import { LeavePolicyBuilderPage } from './pages/organization-setup/LeavePolicyBuilderPage';
import { HolidaysPage } from './pages/organization-setup/HolidaysPage';
import { MasterPage } from './pages/organization-setup/MasterPage';
import { OrganizationSetupLayout } from './pages/organization-setup/OrganizationSetupPage';
import { OrganizationSetupOverviewPage } from './pages/organization-setup/OrganizationSetupOverviewPage';
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
              <Route path="/auth/change-password" element={<ChangePasswordPage />} />
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
              <Route path="employees" element={<EmployeesPage />} />
              <Route path="employees/:employeeId" element={<EmployeeDetailPage />} />
              <Route path="leave-approvals" element={<LeaveApprovalsPage />} />
              <Route path="attendance" element={<AttendancePage />} />
              <Route path="attendance-approvals" element={<AttendanceApprovalsPage />} />
              <Route path="organization" element={<OrganizationEditPage />} />
              <Route path="setup" element={<OrganizationSetupLayout />}>
                <Route index element={<OrganizationSetupOverviewPage />} />
                <Route path="departments" element={<MasterPage masterKey="departments" />} />
                <Route path="designations" element={<DesignationsPage />} />
                <Route path="employee-types" element={<MasterPage masterKey="employee-types" />} />
                <Route path="access-types" element={<MasterPage masterKey="access-types" />} />
                <Route path="shifts" element={<MasterPage masterKey="shifts" />} />
                <Route path="work-weeks" element={<MasterPage masterKey="work-weeks" />} />
                <Route path="leave-types" element={<MasterPage masterKey="leave-types" />} />
                <Route path="holidays" element={<HolidaysPage />} />
                <Route path="documents" element={<DocumentsPage />} />
                <Route path="document-policies" element={<DocumentPoliciesPage />} />
                <Route path="document-policies/new" element={<DocumentPolicyBuilderPage />} />
                <Route path="document-policies/:policyId" element={<DocumentPolicyBuilderPage />} />
                <Route path="assets" element={<AssetsPage />} />
                <Route path="leave-policies" element={<LeavePoliciesPage />} />
                <Route path="leave-policies/new" element={<LeavePolicyBuilderPage />} />
                <Route path="leave-policies/:policyId" element={<LeavePolicyBuilderPage />} />
              </Route>
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
