import { type FormEvent, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { organizationApi } from '../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { tokenStorage } from '../auth/tokenStorage';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { FormField } from '../components/FormField';
import { PasswordInput } from '../components/PasswordInput';
import './LoginPage.css';

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const verified = params.get('verified') === '1';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const infoMessage = useMemo(
    () =>
      verified
        ? 'Your email has been verified. Sign in to create your organization.'
        : null,
    [verified],
  );

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setServerError(null);
    setFieldErrors({});

    if (!email.trim() || !password) {
      setServerError('Email and password are required.');
      return;
    }

    try {
      await auth.login(email.trim(), password, rememberMe);
      const token = tokenStorage.getAccessToken();
      if (token) {
        try {
          const status = await organizationApi.getSetupStatus(token);
          if (status.needs_setup) {
            navigate('/organizations/create');
            return;
          }
        } catch {
          // fall through
        }
      }
      navigate('/app');
    } catch (error) {
      const fields = extractFieldErrors(error);
      setFieldErrors(fields);
      setServerError(
        fields.email || fields.password || extractErrorMessage(error, 'Unable to sign in.'),
      );
    }
  }

  return (
    <Card
      className="login-card"
      footer={
        <div className="login-footer">
          <p>
            Don&apos;t have an account?
            <Link to="/auth/register" className="login-footer__create">
              Create account
            </Link>
          </p>
        </div>
      }
    >
      <div className="login-header">
        <h2>Sign in</h2>
        <p>Welcome back. Enter your work email to continue.</p>
      </div>

      <form className="login-form" onSubmit={onSubmit} noValidate>
        {infoMessage ? (
          <div className="auth-alert auth-alert--success" role="status">
            {infoMessage}
          </div>
        ) : null}
        {serverError ? (
          <div className="auth-alert auth-alert--error" role="alert">
            {serverError}
          </div>
        ) : null}

        <FormField
          id="login-email"
          label="Email"
          type="email"
          autoComplete="email"
          placeholder="you@company.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={fieldErrors.email}
        />

        <div className="login-password-block">
          <PasswordInput
            id="login-password"
            label="Password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            error={fieldErrors.password}
          />
          <Link to="/auth/forgot-password" className="login-forgot">
            Forgot password?
          </Link>
        </div>

        <label className="login-remember">
          <input
            type="checkbox"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
          />
          <span>Remember me</span>
        </label>

        <Button type="submit" fullWidth loading={auth.loading}>
          Sign in
        </Button>
      </form>

      <div className="login-sso" aria-label="Social sign in options">
        <div className="login-sso__divider">
          <span>Or</span>
        </div>
        <div className="login-sso__actions">
          <button type="button" className="sso-btn" disabled title="Coming soon" aria-disabled="true">
            <svg className="sso-btn__icon" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="#F25022" d="M11.4 11.4H2V2h9.4v9.4z" />
              <path fill="#7FBA00" d="M22 11.4h-9.4V2H22v9.4z" />
              <path fill="#00A4EF" d="M11.4 22H2v-9.4h9.4V22z" />
              <path fill="#FFB900" d="M22 22h-9.4v-9.4H22V22z" />
            </svg>
            Microsoft
          </button>
          <button type="button" className="sso-btn" disabled title="Coming soon" aria-disabled="true">
            <svg className="sso-btn__icon" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18A10.96 10.96 0 0 0 1 12c0 1.77.42 3.45 1.18 4.93l3.66-2.84z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Google
          </button>
        </div>
      </div>
    </Card>
  );
}
