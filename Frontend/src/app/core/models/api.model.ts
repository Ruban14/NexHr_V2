export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T | null;
  errors: Record<string, string | string[]> | string[] | null;
}

export interface ApiErrorBody {
  message: string;
  errors?: Record<string, string | string[]> | string[] | null;
  code?: string;
}
