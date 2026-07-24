import { type FormEvent, useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { extractErrorMessage } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { FormField } from '../components/FormField';

export function VerifyEmailPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get('token');

  const [state, setState] = useState<'idle' | 'verifying' | 'success' | 'error'>(
    token ? 'verifying' : 'idle',
  );
  const [message, setMessage] = useState('');
  const [email, setEmail] = useState('');

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    async function run() {
      try {
        await auth.verifyEmail(token!);
        if (cancelled) return;
        setState('success');
        setMessage('Your email has been verified. Sign in to create your organization…');
        navigate('/auth/login?verified=1', { replace: true });
      } catch (err) {
        if (cancelled) return;
        setState('error');
        setMessage(extractErrorMessage(err, 'Verification link is invalid or expired.'));
      }
    }

    void run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function resend(event: FormEvent) {
    event.preventDefault();
    try {
      await auth.resendVerification(email.trim());
      setMessage('If an account exists for that email, a new verification link has been sent.');
    } catch (err) {
      setMessage(extractErrorMessage(err, 'Unable to resend verification email.'));
    }
  }

  return (
    <Card
      footer={
        <p>
          Ready to continue? <Link to="/auth/login">Sign in</Link>
        </p>
      }
    >
      <div className="auth-page__header">
        <h2>Verify email</h2>
        <p>Confirm your email address to activate your account.</p>
      </div>

      {state === 'verifying' ? (
        <div className="auth-alert auth-alert--info">Verifying your email…</div>
      ) : null}
      {message ? (
        <div
          className={`auth-alert ${state === 'error' ? 'auth-alert--error' : 'auth-alert--success'}`}
        >
          {message}
        </div>
      ) : null}

      {!token || state === 'error' ? (
        <form className="auth-form" onSubmit={resend}>
          <FormField
            id="resend-email"
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Button type="submit" fullWidth loading={auth.loading}>
            Resend verification
          </Button>
        </form>
      ) : null}
      <style>{`.auth-form{display:flex;flex-direction:column;gap:1rem}`}</style>
    </Card>
  );
}
