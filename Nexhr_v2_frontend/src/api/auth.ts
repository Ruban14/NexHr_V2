import { apiRequest, buildQuery } from './client';
import type {
  AccessType,
  AssetRecord,
  AssetType,
  AttendanceListResponse,
  AttendanceRecord,
  AttendanceSession,
  BranchMembership,
  Department,
  Designation,
  DocumentCategory,
  DocumentDefinition,
  DocumentPolicy,
  DocumentCompliance,
  EmployeeAssetAssignment,
  EmployeeDocumentRecord,
  EmployeeCreateRequest,
  EmployeeLeaveBalance,
  EmployeeLeaveLog,
  EmployeeRecord,
  EmployeeType,
  Holiday,
  HolidayCalendar,
  IndustryType,
  LeaveApplication,
  LeavePolicy,
  LeaveType,
  LoginResponse,
  MasterListParams,
  Organization,
  OrganizationCreateRequest,
  OrganizationCreateResponse,
  OrganizationSetupStatus,
  OrganizationUpdateRequest,
  PaginatedResponse,
  RegisterResponse,
  Shift,
  User,
  UserProfileDetail,
  UserProfileUpdateRequest,
  WorkWeek,
} from '../types';

export const authApi = {
  register: (payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => apiRequest<RegisterResponse>('/auth/register', { body: payload, skipAuth: true }),

  login: (payload: { email: string; password: string }) =>
    apiRequest<LoginResponse>('/auth/login', { body: payload, skipAuth: true }),

  logout: (refresh: string, token: string) =>
    apiRequest<void>('/auth/logout', { body: { refresh }, token }),

  refresh: (refresh: string) =>
    apiRequest<{ access: string; refresh: string }>('/auth/refresh', {
      body: { refresh },
      skipAuth: true,
    }),

  forgotPassword: (email: string) =>
    apiRequest<void>('/auth/forgot-password', { body: { email }, skipAuth: true }),

  resetPassword: (payload: { token: string; password: string }) =>
    apiRequest<void>('/auth/reset-password', { body: payload, skipAuth: true }),

  changePassword: (
    token: string,
    payload: { current_password: string; password: string },
  ) => apiRequest<User>('/auth/change-password', { body: payload, token }),

  verifyEmail: (token: string) =>
    apiRequest<void>('/auth/verify-email', { body: { token }, skipAuth: true }),

  resendVerification: (email: string) =>
    apiRequest<void>('/auth/resend-verification', { body: { email }, skipAuth: true }),

  me: (token: string) => apiRequest<User>('/auth/me', { token }),
};

export const organizationApi = {
  listIndustryTypes: (token: string) =>
    apiRequest<IndustryType[]>('/organization/industry-types', { token }),

  getSetupStatus: (token: string) =>
    apiRequest<OrganizationSetupStatus>('/organization/setup-status', { token }),

  createOrganization: (token: string, payload: OrganizationCreateRequest) =>
    apiRequest<OrganizationCreateResponse>('/organization/create', { token, body: payload }),

  getCurrent: (token: string) => apiRequest<Organization>('/organization/current', { token }),

  updateCurrent: (token: string, payload: OrganizationUpdateRequest) =>
    apiRequest<Organization>('/organization/current', {
      token,
      method: 'PATCH',
      body: payload,
    }),

  getProfile: (token: string) => apiRequest<UserProfileDetail>('/organization/profile', { token }),

  updateProfile: (token: string, payload: FormData | UserProfileUpdateRequest) =>
    apiRequest<UserProfileDetail>('/organization/profile', {
      token,
      method: 'PATCH',
      body: payload,
    }),

  listBranches: (token: string) =>
    apiRequest<BranchMembership[]>('/organization/branches', { token }),

  listDepartments: (token: string, params: MasterListParams = {}) =>
    apiRequest<PaginatedResponse<Department>>(
      `/organization/departments${buildQuery(params)}`,
      { token },
    ),

  createDepartment: (token: string, payload: { name: string }) =>
    apiRequest<Department>('/organization/departments', { token, body: payload }),

  updateDepartment: (token: string, id: string, payload: { name?: string; is_active?: boolean }) =>
    apiRequest<Department>(`/organization/departments/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteDepartment: (token: string, id: string) =>
    apiRequest<void>(`/organization/departments/${id}`, { token, method: 'DELETE' }),

  listDesignations: (token: string, departmentId: string, search = '') =>
    apiRequest<Designation[]>(
      `/organization/departments/${departmentId}/designations${buildQuery({ search })}`,
      { token },
    ),

  createDesignation: (
    token: string,
    departmentId: string,
    payload: { name: string; parent_id?: string | null },
  ) =>
    apiRequest<Designation>(`/organization/departments/${departmentId}/designations`, {
      token,
      body: payload,
    }),

  updateDesignation: (
    token: string,
    id: string,
    payload: { name?: string; parent_id?: string | null; is_active?: boolean },
  ) =>
    apiRequest<Designation>(`/organization/designations/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteDesignation: (token: string, id: string) =>
    apiRequest<void>(`/organization/designations/${id}`, { token, method: 'DELETE' }),

  moveDesignation: (token: string, id: string, direction: 'up' | 'down') =>
    apiRequest<Designation[]>(`/organization/designations/${id}/move`, {
      token,
      body: { direction },
    }),

  repositionDesignation: (
    token: string,
    id: string,
    payload: { target_id: string; position: 'before' | 'after' | 'inside' },
  ) =>
    apiRequest<Designation[]>(`/organization/designations/${id}/reposition`, {
      token,
      body: payload,
    }),

  listEmployeeTypes: (token: string, params: MasterListParams = {}) =>
    apiRequest<PaginatedResponse<EmployeeType>>(
      `/organization/employee-types${buildQuery(params)}`,
      { token },
    ),

  createEmployeeType: (token: string, payload: { name: string }) =>
    apiRequest<EmployeeType>('/organization/employee-types', { token, body: payload }),

  updateEmployeeType: (token: string, id: string, payload: { name?: string; is_active?: boolean }) =>
    apiRequest<EmployeeType>(`/organization/employee-types/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteEmployeeType: (token: string, id: string) =>
    apiRequest<void>(`/organization/employee-types/${id}`, { token, method: 'DELETE' }),

  listAccessTypes: (token: string, params: MasterListParams = {}) =>
    apiRequest<PaginatedResponse<AccessType>>(
      `/organization/access-types${buildQuery(params)}`,
      { token },
    ),

  createAccessType: (token: string, payload: { name: string; description?: string }) =>
    apiRequest<AccessType>('/organization/access-types', { token, body: payload }),

  updateAccessType: (
    token: string,
    id: string,
    payload: { name?: string; description?: string; is_active?: boolean },
  ) =>
    apiRequest<AccessType>(`/organization/access-types/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteAccessType: (token: string, id: string) =>
    apiRequest<void>(`/organization/access-types/${id}`, { token, method: 'DELETE' }),

  listShifts: (token: string, params: MasterListParams = {}) =>
    apiRequest<PaginatedResponse<Shift>>(`/organization/shifts${buildQuery(params)}`, { token }),

  createShift: (
    token: string,
    payload: { name: string; start_time: string; end_time: string },
  ) => apiRequest<Shift>('/organization/shifts', { token, body: payload }),

  updateShift: (
    token: string,
    id: string,
    payload: { name?: string; start_time?: string; end_time?: string; is_active?: boolean },
  ) =>
    apiRequest<Shift>(`/organization/shifts/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteShift: (token: string, id: string) =>
    apiRequest<void>(`/organization/shifts/${id}`, { token, method: 'DELETE' }),

  listWorkWeeks: (token: string, params: MasterListParams = {}) =>
    apiRequest<PaginatedResponse<WorkWeek>>(
      `/organization/work-weeks${buildQuery(params)}`,
      { token },
    ),

  createWorkWeek: (token: string, payload: { name: string; working_days: number[] }) =>
    apiRequest<WorkWeek>('/organization/work-weeks', { token, body: payload }),

  updateWorkWeek: (
    token: string,
    id: string,
    payload: { name?: string; working_days?: number[]; is_active?: boolean },
  ) =>
    apiRequest<WorkWeek>(`/organization/work-weeks/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteWorkWeek: (token: string, id: string) =>
    apiRequest<void>(`/organization/work-weeks/${id}`, { token, method: 'DELETE' }),

  listLeaveTypes: (token: string, params: MasterListParams = {}) =>
    apiRequest<PaginatedResponse<LeaveType>>(
      `/organization/leave-types${buildQuery(params)}`,
      { token },
    ),

  createLeaveType: (token: string, payload: { name: string }) =>
    apiRequest<LeaveType>('/organization/leave-types', { token, body: payload }),

  updateLeaveType: (token: string, id: string, payload: { name?: string; is_active?: boolean }) =>
    apiRequest<LeaveType>(`/organization/leave-types/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteLeaveType: (token: string, id: string) =>
    apiRequest<void>(`/organization/leave-types/${id}`, { token, method: 'DELETE' }),

  listHolidayCalendars: (
    token: string,
    params: MasterListParams & { year?: number } = {},
  ) =>
    apiRequest<PaginatedResponse<HolidayCalendar>>(
      `/organization/holiday-calendars${buildQuery(params)}`,
      { token },
    ),

  createHolidayCalendar: (token: string, payload: { name: string; year: number }) =>
    apiRequest<HolidayCalendar>('/organization/holiday-calendars', { token, body: payload }),

  updateHolidayCalendar: (
    token: string,
    id: string,
    payload: { name?: string; year?: number; is_active?: boolean },
  ) =>
    apiRequest<HolidayCalendar>(`/organization/holiday-calendars/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteHolidayCalendar: (token: string, id: string) =>
    apiRequest<void>(`/organization/holiday-calendars/${id}`, { token, method: 'DELETE' }),

  listHolidays: (token: string, calendarId: string, search = '') =>
    apiRequest<Holiday[]>(
      `/organization/holiday-calendars/${calendarId}/holidays${buildQuery({ search })}`,
      { token },
    ),

  createHoliday: (token: string, calendarId: string, payload: { name: string; date: string }) =>
    apiRequest<Holiday>(`/organization/holiday-calendars/${calendarId}/holidays`, {
      token,
      body: payload,
    }),

  updateHoliday: (
    token: string,
    id: string,
    payload: { name?: string; date?: string },
  ) =>
    apiRequest<Holiday>(`/organization/holidays/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteHoliday: (token: string, id: string) =>
    apiRequest<void>(`/organization/holidays/${id}`, { token, method: 'DELETE' }),

  listDocumentCategories: (token: string, params: { search?: string; is_active?: boolean } = {}) =>
    apiRequest<DocumentCategory[]>(
      `/organization/document-categories${buildQuery(params)}`,
      { token },
    ),

  createDocumentCategory: (
    token: string,
    payload: { name: string; description?: string; display_order?: number },
  ) => apiRequest<DocumentCategory>('/organization/document-categories', { token, body: payload }),

  updateDocumentCategory: (
    token: string,
    id: string,
    payload: { name?: string; description?: string; display_order?: number; is_active?: boolean },
  ) =>
    apiRequest<DocumentCategory>(`/organization/document-categories/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  listDocumentDefinitions: (
    token: string,
    params: MasterListParams & { category_id?: string } = {},
  ) =>
    apiRequest<PaginatedResponse<DocumentDefinition>>(
      `/organization/document-definitions${buildQuery(params)}`,
      { token },
    ),

  createDocumentDefinition: (
    token: string,
    payload: { name: string; category_id: string; description?: string },
  ) => apiRequest<DocumentDefinition>('/organization/document-definitions', { token, body: payload }),

  updateDocumentDefinition: (
    token: string,
    id: string,
    payload: {
      name?: string;
      category_id?: string;
      description?: string;
      is_active?: boolean;
    },
  ) =>
    apiRequest<DocumentDefinition>(`/organization/document-definitions/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteDocumentDefinition: (token: string, id: string) =>
    apiRequest<void>(`/organization/document-definitions/${id}`, { token, method: 'DELETE' }),

  listDocumentPolicies: (
    token: string,
    params: MasterListParams & { employee_type_id?: string } = {},
  ) =>
    apiRequest<PaginatedResponse<DocumentPolicy>>(
      `/organization/document-policies${buildQuery(params)}`,
      { token },
    ),

  getDocumentPolicy: (token: string, id: string) =>
    apiRequest<DocumentPolicy>(`/organization/document-policies/${id}`, { token }),

  createDocumentPolicy: (
    token: string,
    payload: {
      name: string;
      employee_type_id: string;
      description?: string;
      is_default?: boolean;
      items?: Array<{
        document_id: string;
        display_order?: number;
        is_required?: boolean;
        allow_multiple?: boolean;
        verification_required?: boolean;
        requires_expiry?: boolean;
      }>;
    },
  ) => apiRequest<DocumentPolicy>('/organization/document-policies', { token, body: payload }),

  updateDocumentPolicy: (
    token: string,
    id: string,
    payload: {
      name?: string;
      employee_type_id?: string;
      description?: string;
      is_default?: boolean;
      is_active?: boolean;
      items?: Array<{
        document_id: string;
        display_order?: number;
        is_required?: boolean;
        allow_multiple?: boolean;
        verification_required?: boolean;
        requires_expiry?: boolean;
      }>;
    },
  ) =>
    apiRequest<DocumentPolicy>(`/organization/document-policies/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteDocumentPolicy: (token: string, id: string) =>
    apiRequest<void>(`/organization/document-policies/${id}`, { token, method: 'DELETE' }),

  listEmployeeDocuments: (token: string, employeeId: string) =>
    apiRequest<EmployeeDocumentRecord[]>(`/organization/employees/${employeeId}/documents`, {
      token,
    }),

  checkEmployeeDocumentCompliance: (token: string, employeeId: string) =>
    apiRequest<DocumentCompliance>(
      `/organization/employees/${employeeId}/documents/compliance`,
      { token },
    ),

  uploadEmployeeDocument: (token: string, employeeId: string, payload: FormData) =>
    apiRequest<EmployeeDocumentRecord>(`/organization/employees/${employeeId}/documents`, {
      token,
      body: payload,
    }),

  reviewEmployeeDocument: (
    token: string,
    employeeId: string,
    documentId: string,
    payload: { approve: boolean; remarks?: string },
  ) =>
    apiRequest<EmployeeDocumentRecord>(
      `/organization/employees/${employeeId}/documents/${documentId}/review`,
      { token, body: payload },
    ),

  deleteEmployeeDocument: (token: string, employeeId: string, documentId: string) =>
    apiRequest<void>(`/organization/employees/${employeeId}/documents/${documentId}`, {
      token,
      method: 'DELETE',
    }),

  listAssetTypes: (token: string, params: { is_active?: boolean } = {}) =>
    apiRequest<AssetType[]>(`/organization/asset-types${buildQuery(params)}`, { token }),

  createAssetType: (
    token: string,
    payload: { name: string; description?: string },
  ) => apiRequest<AssetType>('/organization/asset-types', { token, body: payload }),

  updateAssetType: (
    token: string,
    id: string,
    payload: { name?: string; description?: string; is_active?: boolean },
  ) =>
    apiRequest<AssetType>(`/organization/asset-types/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteAssetType: (token: string, id: string) =>
    apiRequest<void>(`/organization/asset-types/${id}`, { token, method: 'DELETE' }),

  listAssets: (
    token: string,
    params: MasterListParams & { asset_type_id?: string; status?: string } = {},
  ) =>
    apiRequest<PaginatedResponse<AssetRecord>>(
      `/organization/assets${buildQuery(params)}`,
      { token },
    ),

  listAvailableAssets: (token: string, search = '') =>
    apiRequest<AssetRecord[]>(
      `/organization/assets/available${buildQuery({ search: search || undefined })}`,
      { token },
    ),

  createAsset: (
    token: string,
    payload: {
      asset_type_id: string;
      asset_code: string;
      name: string;
      brand?: string;
      model?: string;
      serial_number?: string;
      purchase_date?: string | null;
      warranty_expiry?: string | null;
      status?: string;
      remarks?: string;
    },
  ) => apiRequest<AssetRecord>('/organization/assets', { token, body: payload }),

  updateAsset: (
    token: string,
    id: string,
    payload: {
      asset_type_id?: string;
      asset_code?: string;
      name?: string;
      brand?: string;
      model?: string;
      serial_number?: string;
      purchase_date?: string | null;
      warranty_expiry?: string | null;
      status?: string;
      remarks?: string;
      is_active?: boolean;
    },
  ) =>
    apiRequest<AssetRecord>(`/organization/assets/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteAsset: (token: string, id: string) =>
    apiRequest<void>(`/organization/assets/${id}`, { token, method: 'DELETE' }),

  listEmployeeAssetAssignments: (token: string, employeeId: string) =>
    apiRequest<EmployeeAssetAssignment[]>(
      `/organization/employees/${employeeId}/asset-assignments`,
      { token },
    ),

  assignEmployeeAsset: (
    token: string,
    employeeId: string,
    payload: {
      asset_id: string;
      assigned_at?: string | null;
      expected_return_at?: string | null;
      remarks?: string;
    },
  ) =>
    apiRequest<EmployeeAssetAssignment>(
      `/organization/employees/${employeeId}/asset-assignments`,
      { token, body: payload },
    ),

  revokeEmployeeAsset: (
    token: string,
    employeeId: string,
    assignmentId: string,
    payload: { returned_at?: string | null; remarks?: string; mark_lost?: boolean } = {},
  ) =>
    apiRequest<EmployeeAssetAssignment>(
      `/organization/employees/${employeeId}/asset-assignments/${assignmentId}/revoke`,
      { token, body: payload },
    ),

  listLeavePolicies: (
    token: string,
    params: MasterListParams & { employee_type_id?: string } = {},
  ) =>
    apiRequest<PaginatedResponse<LeavePolicy>>(
      `/organization/leave-policies${buildQuery(params)}`,
      { token },
    ),

  getLeavePolicy: (token: string, id: string) =>
    apiRequest<LeavePolicy>(`/organization/leave-policies/${id}`, { token }),

  createLeavePolicy: (
    token: string,
    payload: {
      code: string;
      name: string;
      employee_type_id: string;
      description?: string;
      effective_from: string;
      effective_to?: string | null;
      is_default?: boolean;
      rules?: Array<{
        leave_type_id: string;
        allocation_frequency?: string;
        allocation_quantity?: string | number;
        annual_limit?: string | number;
        carry_forward_allowed?: boolean;
        carry_forward_limit?: string | number;
        encashment_allowed?: boolean;
        encashment_limit?: string | number;
        allow_half_day?: boolean;
        allow_negative_balance?: boolean;
        minimum_service_days?: number;
        maximum_consecutive_days?: number | null;
        is_active?: boolean;
      }>;
    },
  ) => apiRequest<LeavePolicy>('/organization/leave-policies', { token, body: payload }),

  updateLeavePolicy: (
    token: string,
    id: string,
    payload: {
      code?: string;
      name?: string;
      employee_type_id?: string;
      description?: string;
      effective_from?: string;
      effective_to?: string | null;
      is_default?: boolean;
      is_active?: boolean;
      rules?: Array<{
        leave_type_id: string;
        allocation_frequency?: string;
        allocation_quantity?: string | number;
        annual_limit?: string | number;
        carry_forward_allowed?: boolean;
        carry_forward_limit?: string | number;
        encashment_allowed?: boolean;
        encashment_limit?: string | number;
        allow_half_day?: boolean;
        allow_negative_balance?: boolean;
        minimum_service_days?: number;
        maximum_consecutive_days?: number | null;
        is_active?: boolean;
      }>;
    },
  ) =>
    apiRequest<LeavePolicy>(`/organization/leave-policies/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  deleteLeavePolicy: (token: string, id: string) =>
    apiRequest<void>(`/organization/leave-policies/${id}`, { token, method: 'DELETE' }),

  listEmployeeLeaveBalances: (token: string, employeeId: string) =>
    apiRequest<EmployeeLeaveBalance[]>(
      `/organization/employees/${employeeId}/leave-balances`,
      { token },
    ),

  allocateEmployeeLeave: (
    token: string,
    employeeId: string,
    payload: { leave_type_id: string; quantity: string | number; remarks?: string },
  ) =>
    apiRequest<EmployeeLeaveBalance>(
      `/organization/employees/${employeeId}/leave-balances/allocate`,
      { token, body: payload },
    ),

  adjustEmployeeLeave: (
    token: string,
    employeeId: string,
    payload: { leave_type_id: string; quantity: string | number; remarks?: string },
  ) =>
    apiRequest<EmployeeLeaveBalance>(
      `/organization/employees/${employeeId}/leave-balances/adjust`,
      { token, body: payload },
    ),

  seedEmployeeLeaveBalances: (token: string, employeeId: string) =>
    apiRequest<EmployeeLeaveBalance[]>(
      `/organization/employees/${employeeId}/leave-balances/seed`,
      { token, body: {} },
    ),

  listEmployeeLeaveApplications: (token: string, employeeId: string, status?: string) =>
    apiRequest<LeaveApplication[]>(
      `/organization/employees/${employeeId}/leave-applications${buildQuery({
        status: status || undefined,
      })}`,
      { token },
    ),

  createEmployeeLeaveApplication: (token: string, employeeId: string, payload: FormData) =>
    apiRequest<LeaveApplication>(`/organization/employees/${employeeId}/leave-applications`, {
      token,
      body: payload,
    }),

  reviewEmployeeLeaveApplication: (
    token: string,
    employeeId: string,
    applicationId: string,
    payload: { approve: boolean; remarks?: string },
  ) =>
    apiRequest<LeaveApplication>(
      `/organization/employees/${employeeId}/leave-applications/${applicationId}/review`,
      { token, body: payload },
    ),

  listLeaveApprovals: (token: string, status?: string) =>
    apiRequest<{ pending_count: number; items: LeaveApplication[] }>(
      `/organization/leave-approvals${buildQuery({ status: status || undefined })}`,
      { token },
    ),

  reviewLeaveApproval: (
    token: string,
    applicationId: string,
    payload: { approve: boolean; remarks?: string },
  ) =>
    apiRequest<LeaveApplication>(`/organization/leave-approvals/${applicationId}/review`, {
      token,
      body: payload,
    }),

  cancelEmployeeLeaveApplication: (
    token: string,
    employeeId: string,
    applicationId: string,
    payload: { remarks?: string } = {},
  ) =>
    apiRequest<LeaveApplication>(
      `/organization/employees/${employeeId}/leave-applications/${applicationId}/cancel`,
      { token, body: payload },
    ),

  listEmployeeLeaveLogs: (token: string, employeeId: string) =>
    apiRequest<EmployeeLeaveLog[]>(`/organization/employees/${employeeId}/leave-logs`, {
      token,
    }),

  listAttendance: (
    token: string,
    params: {
      date?: string;
      date_from?: string;
      date_to?: string;
      status?: string;
      employee_id?: string;
      search?: string;
    } = {},
  ) =>
    apiRequest<AttendanceListResponse>(`/organization/attendance${buildQuery(params)}`, {
      token,
    }),

  getTodayAttendance: (token: string, employeeId?: string) =>
    apiRequest<AttendanceRecord>(
      `/organization/attendance/today${buildQuery({
        employee_id: employeeId || undefined,
      })}`,
      { token },
    ),

  getAttendanceDetail: (token: string, attendanceId: string) =>
    apiRequest<AttendanceRecord>(`/organization/attendance/${attendanceId}`, { token }),

  attendanceCheckIn: (token: string, payload: { remarks?: string; source?: string } = {}) =>
    apiRequest<AttendanceRecord>('/organization/attendance/check-in', { token, body: payload }),

  attendanceCheckOut: (token: string, payload: { remarks?: string } = {}) =>
    apiRequest<AttendanceRecord>('/organization/attendance/check-out', { token, body: payload }),

  attendanceBreakStart: (token: string, payload: { remarks?: string } = {}) =>
    apiRequest<AttendanceRecord>('/organization/attendance/break-start', { token, body: payload }),

  attendanceBreakEnd: (token: string, payload: { remarks?: string } = {}) =>
    apiRequest<AttendanceRecord>('/organization/attendance/break-end', { token, body: payload }),

  listEmployeeAttendance: (
    token: string,
    employeeId: string,
    params: { date_from?: string; date_to?: string } = {},
  ) =>
    apiRequest<AttendanceRecord[]>(
      `/organization/employees/${employeeId}/attendance${buildQuery(params)}`,
      { token },
    ),

  listEmployeeAttendanceSessions: (
    token: string,
    employeeId: string,
    params: { date_from?: string; date_to?: string } = {},
  ) =>
    apiRequest<AttendanceSession[]>(
      `/organization/employees/${employeeId}/attendance/sessions${buildQuery(params)}`,
      { token },
    ),

  employeeAttendanceCheckIn: (
    token: string,
    employeeId: string,
    payload: { remarks?: string; source?: string } = {},
  ) =>
    apiRequest<AttendanceRecord>(`/organization/employees/${employeeId}/attendance/check-in`, {
      token,
      body: payload,
    }),

  employeeAttendanceCheckOut: (
    token: string,
    employeeId: string,
    payload: { remarks?: string } = {},
  ) =>
    apiRequest<AttendanceRecord>(`/organization/employees/${employeeId}/attendance/check-out`, {
      token,
      body: payload,
    }),

  employeeAttendanceBreakStart: (
    token: string,
    employeeId: string,
    payload: { remarks?: string } = {},
  ) =>
    apiRequest<AttendanceRecord>(`/organization/employees/${employeeId}/attendance/break-start`, {
      token,
      body: payload,
    }),

  employeeAttendanceBreakEnd: (
    token: string,
    employeeId: string,
    payload: { remarks?: string } = {},
  ) =>
    apiRequest<AttendanceRecord>(`/organization/employees/${employeeId}/attendance/break-end`, {
      token,
      body: payload,
    }),

  manualEmployeeAttendance: (
    token: string,
    employeeId: string,
    payload: {
      attendance_date: string;
      status?: string;
      check_in?: string | null;
      check_out?: string | null;
      remarks?: string;
      session_remarks?: string;
    },
  ) =>
    apiRequest<AttendanceRecord>(`/organization/employees/${employeeId}/attendance/manual`, {
      token,
      body: payload,
    }),

  listAttendanceApprovals: (token: string, status?: string) =>
    apiRequest<{ pending_count: number; items: AttendanceRecord[] }>(
      `/organization/attendance-approvals${buildQuery({ status: status || undefined })}`,
      { token },
    ),

  reviewAttendanceApproval: (
    token: string,
    attendanceId: string,
    payload: { approve: boolean; remarks?: string },
  ) =>
    apiRequest<AttendanceRecord>(`/organization/attendance-approvals/${attendanceId}/review`, {
      token,
      body: payload,
    }),

  listEmployees: (
    token: string,
    params: MasterListParams & { lifecycle_status_id?: string } = {},
  ) =>
    apiRequest<PaginatedResponse<EmployeeRecord>>(
      `/organization/employees${buildQuery(params)}`,
      { token },
    ),

  getEmployee: (token: string, id: string) =>
    apiRequest<EmployeeRecord>(`/organization/employees/${id}`, { token }),

  createEmployee: (token: string, payload: EmployeeCreateRequest) =>
    apiRequest<EmployeeRecord>('/organization/employees', { token, body: payload }),

  updateEmployee: (token: string, id: string, payload: FormData | Record<string, unknown>) =>
    apiRequest<EmployeeRecord>(`/organization/employees/${id}`, {
      token,
      method: 'PATCH',
      body: payload,
    }),

  transitionEmployee: (
    token: string,
    id: string,
    payload: { to_status_id: string; remarks?: string; exit_date?: string },
  ) =>
    apiRequest<EmployeeRecord>(`/organization/employees/${id}/transition`, {
      token,
      body: payload,
    }),
};
