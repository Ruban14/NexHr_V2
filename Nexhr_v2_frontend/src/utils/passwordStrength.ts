export type PasswordStrength = {
  score: number;
  label: 'Weak' | 'Fair' | 'Good' | 'Strong';
  checks: {
    length: boolean;
    uppercase: boolean;
    lowercase: boolean;
    number: boolean;
    special: boolean;
  };
};

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
