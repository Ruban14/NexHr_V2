import { type FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { extractErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { FormField } from '../../components/FormField';

export function ForgotPasswordPage() {
  const auth = useAuth();
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      await auth.forgotPassword(email.trim());
      setMessage('If an account exists for that email, password reset instructions were sent.');
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to send reset email.'));
    }
  }

  return (
    <Card
      footer={
        <p>
          Remembered your password? <Link to="/auth/login">Sign in</Link>
        </p>
      }
    >
      <div className="auth-page__header">
        <h2>Forgot password</h2>
        <p>Enter your work email and we&apos;ll send a reset link.</p>
      </div>
      <form className="auth-form" onSubmit={onSubmit}>
        {message ? <div className="auth-alert auth-alert--success">{message}</div> : null}
        {error ? <div className="auth-alert auth-alert--error">{error}</div> : null}
        <FormField
          id="forgot-email"
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <Button type="submit" fullWidth loading={auth.loading}>
          Send reset link
        </Button>
      </form>
      <style>{`.auth-form{display:flex;flex-direction:column;gap:1rem}`}</style>
    </Card>
  );
}
