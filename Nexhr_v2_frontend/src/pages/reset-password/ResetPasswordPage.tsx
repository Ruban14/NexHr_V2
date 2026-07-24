import { type FormEvent, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { extractErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { PasswordInput } from '../../components/PasswordInput';

export function ResetPasswordPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const token = params.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!token) {
      setError('Reset token is missing.');
      return;
    }
    if (password.length < 9) {
      setError('Password must be at least 9 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    try {
      await auth.resetPassword(token, password);
      navigate('/auth/login');
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to reset password.'));
    }
  }

  return (
    <Card
      footer={
        <p>
          Back to <Link to="/auth/login">Sign in</Link>
        </p>
      }
    >
      <div className="auth-page__header">
        <h2>Reset password</h2>
        <p>Choose a new password for your account.</p>
      </div>
      <form className="auth-form" onSubmit={onSubmit}>
        {error ? <div className="auth-alert auth-alert--error">{error}</div> : null}
        <PasswordInput
          id="reset-password"
          label="New password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <PasswordInput
          id="reset-password-confirm"
          label="Confirm password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
        />
        <Button type="submit" fullWidth loading={auth.loading}>
          Update password
        </Button>
      </form>
      <style>{`.auth-form{display:flex;flex-direction:column;gap:1rem}`}</style>
    </Card>
  );
}
