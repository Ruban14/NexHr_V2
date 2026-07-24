import { apiRequest } from './client';
import type {
  LoginResponse,
  Organization,
  OrganizationCreateRequest,
  OrganizationCreateResponse,
  OrganizationSetupStatus,
  OrganizationUpdateRequest,
  IndustryType,
  RegisterResponse,
  User,
  UserProfileDetail,
  UserProfileUpdateRequest,
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
};
