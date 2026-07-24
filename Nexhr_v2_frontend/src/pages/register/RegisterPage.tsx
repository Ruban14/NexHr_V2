import { type FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { FormField } from '../../components/FormField';
import { PasswordInput } from '../../components/PasswordInput';
import { PasswordStrength } from '../../components/PasswordStrength';
import './RegisterPage.css';

export function RegisterPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [complete, setComplete] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [serverError, setServerError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setServerError(null);
    setFormError(null);
    setFieldErrors({});

    const nextFieldErrors: Record<string, string> = {};
    if (!firstName.trim()) nextFieldErrors.first_name = 'First name is required.';
    if (!lastName.trim()) nextFieldErrors.last_name = 'Last name is required.';
    if (!email.trim()) nextFieldErrors.email = 'Email is required.';
    if (password.length < 9) {
      nextFieldErrors.password = 'Password must be at least 9 characters.';
    }
    if (!confirm) {
      nextFieldErrors.password_confirm = 'Password confirmation is required.';
    } else if (password !== confirm) {
      setFormError('Passwords do not match.');
    }

    if (Object.keys(nextFieldErrors).length > 0 || password !== confirm) {
      setFieldErrors(nextFieldErrors);
      return;
    }

    try {
      await auth.register({
        email: email.trim(),
        password,
        first_name: firstName.trim(),
        last_name: lastName.trim(),
      });
      setRegisteredEmail(email.trim());
      setComplete(true);
    } catch (err) {
      const fields = extractFieldErrors(err);
      setFieldErrors(fields);
      setServerError(
        fields.email ||
          fields.password ||
          fields.first_name ||
          fields.last_name ||
          extractErrorMessage(err, 'Unable to create account.'),
      );
    }
  }

  if (complete) {
    return (
      <Card className="register-card register-card--success">
        <div className="register-success">
          <div className="register-success__icon" aria-hidden="true">
            ✓
          </div>
          <div className="auth-page__header">
            <h2>Verification email sent</h2>
            <p>
              We sent a verification link to <strong>{registeredEmail}</strong>. Open the email and
              confirm your address to activate your account.
            </p>
          </div>

          <div className="auth-alert auth-alert--success" role="status">
            Check your inbox and spam folder. The link expires in 24 hours.
          </div>

          <Button fullWidth onClick={() => navigate('/auth/login')}>
            Continue to sign in
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card
      className="register-card"
      footer={
        <div className="auth-page__footer">
          <span>Already have an account?</span>
          <Link to="/auth/login" className="auth-link">
            Sign in
          </Link>
        </div>
      }
    >
      <div className="auth-page__header">
        <h2>Create your account</h2>
        <p>
          Start with secure credentials. After email verification, you can continue into your
          workspace.
        </p>
      </div>

      <form className="register-form" onSubmit={onSubmit} noValidate>
        {serverError ? (
          <div className="auth-alert auth-alert--error" role="alert">
            {serverError}
          </div>
        ) : null}
        {formError ? (
          <div className="auth-alert auth-alert--error" role="alert">
            {formError}
          </div>
        ) : null}

        <div className="name-grid">
          <FormField
            id="register-first-name"
            label="First name"
            autoComplete="given-name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            error={fieldErrors.first_name}
            required
          />
          <FormField
            id="register-last-name"
            label="Last name"
            autoComplete="family-name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            error={fieldErrors.last_name}
            required
          />
        </div>

        <FormField
          id="register-email"
          label="Work email"
          type="email"
          autoComplete="email"
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={fieldErrors.email}
          required
        />

        <PasswordInput
          id="register-password"
          label="Password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={fieldErrors.password}
          required
        />

        <PasswordStrength password={password} />

        <PasswordInput
          id="register-password-confirm"
          label="Confirm password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={fieldErrors.password_confirm}
          required
        />

        <Button type="submit" fullWidth loading={auth.loading}>
          Create account
        </Button>
      </form>
    </Card>
  );
}
