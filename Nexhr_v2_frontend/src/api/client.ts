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
  branchId?: string | null;
};

let activeBranchId: string | null = null;

export function setActiveBranchId(branchId: string | null) {
  activeBranchId = branchId;
}

export function getActiveBranchId(): string | null {
  return activeBranchId;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

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
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  let payload: ApiResponse<T> | null = null;
  try {
    payload = (await response.json()) as ApiResponse<T>;
  } catch {
    throw new ApiError('Unexpected server response.', response.status);
  }

  if (!response.ok || !payload.success) {
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
  for (const [key, value] of Object.entries(error.errors)) {
    if (typeof value === 'string') {
      result[key] = value;
    } else if (Array.isArray(value) && value.length > 0) {
      result[key] = String(value[0]);
    }
  }
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
