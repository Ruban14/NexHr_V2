import { tokenStorage } from '../auth/tokenStorage';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api';

export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T | null;
  errors: Record<string, unknown> | null;
};

export class ApiError extends Error {
  status: number;
  errors: Record<string, unknown> | null;

  constructor(message: string, status: number, errors: Record<string, unknown> | null = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errors = errors;
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  skipAuth?: boolean;
  /** Prevent recursive refresh attempts on the same request. */
  skipRefresh?: boolean;
  branchId?: string | null;
};

let activeBranchId: string | null = null;
/** Single-flight refresh so parallel 401s share one rotate call. */
let refreshInFlight: Promise<string | null> | null = null;

export function setActiveBranchId(branchId: string | null) {
  activeBranchId = branchId;
}

export function getActiveBranchId(): string | null {
  return activeBranchId;
}

async function refreshAccessToken(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight;

  refreshInFlight = (async () => {
    const refresh = tokenStorage.getRefreshToken();
    if (!refresh) return null;

    try {
      const tokens = await apiRequest<{ access: string; refresh: string }>('/auth/refresh', {
        method: 'POST',
        body: { refresh },
        skipAuth: true,
        skipRefresh: true,
      });
      tokenStorage.setAccessToken(tokens.access);
      tokenStorage.setRefreshToken(tokens.refresh);
      return tokens.access;
    } catch {
      tokenStorage.clear();
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();

  return refreshInFlight;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  if (!options.skipAuth && options.token) {
    headers.Authorization = `Bearer ${options.token}`;
  }

  const branchId = options.branchId === undefined ? activeBranchId : options.branchId;
  if (branchId) {
    headers['X-Branch-Id'] = branchId;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? (options.body ? 'POST' : 'GET'),
    headers,
    body:
      options.body === undefined
        ? undefined
        : isFormData
          ? (options.body as FormData)
          : JSON.stringify(options.body),
  });

  let payload: ApiResponse<T> | null = null;
  try {
    payload = (await response.json()) as ApiResponse<T>;
  } catch {
    throw new ApiError('Unexpected server response.', response.status);
  }

  if (!response.ok || !payload.success) {
    const canRefresh =
      response.status === 401 &&
      !options.skipAuth &&
      !options.skipRefresh &&
      Boolean(tokenStorage.getRefreshToken());

    if (canRefresh) {
      const nextAccess = await refreshAccessToken();
      if (nextAccess) {
        return apiRequest<T>(path, {
          ...options,
          token: nextAccess,
          skipRefresh: true,
        });
      }
    }

    throw new ApiError(
      payload.message || 'Request failed.',
      response.status,
      payload.errors,
    );
  }

  if (payload.data === null) {
    return undefined as T;
  }

  return payload.data;
}

export function extractErrorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  if (error instanceof ApiError) {
    return error.message || fallback;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

export function extractFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || !error.errors || typeof error.errors !== 'object') {
    return {};
  }

  const result: Record<string, string> = {};

  const flatten = (value: unknown, prefix = ''): void => {
    if (value == null) return;
    if (typeof value === 'string') {
      if (prefix) result[prefix] = value;
      return;
    }
    if (Array.isArray(value)) {
      if (value.length === 0) return;
      if (typeof value[0] === 'string' || typeof value[0] === 'number') {
        if (prefix) result[prefix] = String(value[0]);
        return;
      }
      value.forEach((item, index) => flatten(item, prefix ? `${prefix}.${index}` : String(index)));
      return;
    }
    if (typeof value === 'object') {
      for (const [key, nested] of Object.entries(value as Record<string, unknown>)) {
        if (key === 'code') continue;
        flatten(nested, prefix ? `${prefix}.${key}` : key);
      }
    }
  };

  flatten(error.errors);
  return result;
}

export function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue;
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}
