import { evaluatePasswordStrength } from '../utils/passwordStrength';
import './PasswordStrength.css';

export function PasswordStrength({ password }: { password: string }) {
  if (!password) {
    return null;
  }

  const strength = evaluatePasswordStrength(password);
  const labelClass = strength.label.toLowerCase();
  const barWidth = `${(strength.score / 5) * 100}%`;

  return (
    <div className="strength" aria-live="polite">
      <div className="strength__header">
        <span>Password strength</span>
        <span className={`strength__label strength__label--${labelClass}`}>
          {strength.label}
        </span>
      </div>
      <div
        className="strength__bar"
        role="progressbar"
        aria-valuenow={strength.score}
        aria-valuemin={0}
        aria-valuemax={5}
      >
        <span
          className={`strength__fill strength__fill--${labelClass}`}
          style={{ width: barWidth }}
        />
      </div>
      <ul className="strength__checks">
        <li className={strength.checks.length ? 'is-met' : undefined}>More than 8 characters</li>
        <li className={strength.checks.uppercase ? 'is-met' : undefined}>Uppercase letter</li>
        <li className={strength.checks.lowercase ? 'is-met' : undefined}>Lowercase letter</li>
        <li className={strength.checks.number ? 'is-met' : undefined}>Number</li>
        <li className={strength.checks.special ? 'is-met' : undefined}>Special character</li>
      </ul>
    </div>
  );
}
