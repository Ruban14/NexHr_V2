import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

export function passwordMatchValidator(passwordField = 'password', confirmField = 'password_confirm'): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const password = control.get(passwordField)?.value;
    const confirm = control.get(confirmField)?.value;
    if (!password || !confirm) {
      return null;
    }
    return password === confirm ? null : { passwordMismatch: true };
  };
}

export interface PasswordStrength {
  score: number;
  label: 'Weak' | 'Fair' | 'Good' | 'Strong';
  checks: {
    length: boolean;
    uppercase: boolean;
    lowercase: boolean;
    number: boolean;
    special: boolean;
  };
}

export function evaluatePasswordStrength(password: string): PasswordStrength {
  const checks = {
    length: password.length > 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };

  const score = Object.values(checks).filter(Boolean).length;
  const labels: PasswordStrength['label'][] = ['Weak', 'Fair', 'Good', 'Strong'];
  const label = labels[Math.min(Math.max(score - 1, 0), 3)] ?? 'Weak';

  return { score, label, checks };
}

export function getControlErrorMessage(control: AbstractControl | null, fieldLabel: string): string | null {
  if (!control || !control.touched || !control.errors) {
    return null;
  }

  if (control.errors['required']) {
    return `${fieldLabel} is required.`;
  }
  if (control.errors['email']) {
    return 'Enter a valid email address.';
  }
  if (control.errors['minlength']) {
    return `${fieldLabel} must be at least ${control.errors['minlength'].requiredLength} characters.`;
  }
  if (control.errors['maxlength']) {
    return `${fieldLabel} must be at most ${control.errors['maxlength'].requiredLength} characters.`;
  }
  return `${fieldLabel} is invalid.`;
}

export function getFormErrorMessage(errors: ValidationErrors | null): string | null {
  if (!errors) {
    return null;
  }
  if (errors['passwordMismatch']) {
    return 'Passwords do not match.';
  }
  return null;
}

type ApiErrorMap = Record<string, string | string[] | null | undefined>;

function firstDisplayableError(errors: ApiErrorMap): string | null {
  for (const [key, value] of Object.entries(errors)) {
    if (key === 'code' || value == null) {
      continue;
    }

    if (Array.isArray(value)) {
      const candidate = value.find((item): item is string => typeof item === 'string' && item.length > 0);
      if (candidate) {
        return candidate;
      }
      continue;
    }

    if (typeof value === 'string' && value.length > 0) {
      return value;
    }
  }

  return null;
}

export function extractErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as { message?: string; errors?: ApiErrorMap | string[] | null };
    if (apiError.message) {
      if (apiError.errors && !Array.isArray(apiError.errors)) {
        const fieldError = firstDisplayableError(apiError.errors);
        if (fieldError) {
          return fieldError;
        }
      }
      return apiError.message;
    }
  }
  return fallback;
}

export function extractFieldErrors(error: unknown): Record<string, string> {
  if (typeof error === 'object' && error !== null) {
    const apiError = error as { errors?: ApiErrorMap | string[] | null };
    if (apiError.errors && !Array.isArray(apiError.errors)) {
      return Object.fromEntries(
        Object.entries(apiError.errors)
          .filter(([key]) => key !== 'code' && key !== 'locked_until' && key !== 'recovery_action' && key !== 'retry_after_minutes')
          .map(([key, value]) => {
            if (Array.isArray(value)) {
              return [key, value[0] ?? 'Invalid value'];
            }
            if (typeof value === 'string') {
              return [key, value];
            }
            return [key, 'Invalid value'];
          }),
      );
    }
  }
  return {};
}

export interface AccountLockedDetails {
  lockedUntil: string | null;
  retryAfterMinutes: number | null;
  suggestForgotPassword: boolean;
}

export function extractAccountLockedDetails(error: unknown): AccountLockedDetails | null {
  if (typeof error !== 'object' || error === null) {
    return null;
  }

  const apiError = error as { errors?: ApiErrorMap | string[] | null };
  if (!apiError.errors || Array.isArray(apiError.errors) || apiError.errors['code'] !== 'account_locked') {
    return null;
  }

  const lockedUntil = typeof apiError.errors['locked_until'] === 'string' ? apiError.errors['locked_until'] : null;
  const retryAfterMinutes =
    typeof apiError.errors['retry_after_minutes'] === 'number'
      ? apiError.errors['retry_after_minutes']
      : typeof apiError.errors['retry_after_minutes'] === 'string'
        ? Number(apiError.errors['retry_after_minutes'])
        : null;

  return {
    lockedUntil,
    retryAfterMinutes: Number.isFinite(retryAfterMinutes) ? retryAfterMinutes : null,
    suggestForgotPassword:
      apiError.errors['recovery_action'] === 'forgot_password' || lockedUntil !== null,
  };
}
