import { apiRequest, buildQuery } from './client';
import type {
  AccessType,
  BranchMembership,
  Department,
  Designation,
  EmployeeType,
  Holiday,
  HolidayCalendar,
  IndustryType,
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

  updateProfile: (token: string, payload: UserProfileUpdateRequest) =>
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
};
