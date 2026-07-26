import { type FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { PasswordInput } from '../../components/PasswordInput';

export function ChangePasswordPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setFieldErrors({});

    if (password.length < 9) {
      setError('Password must be at least 9 characters.');
      return;
    }
    if (password !== confirm) {
      setError('Passwords do not match.');
      return;
    }

    try {
      await auth.changePassword(currentPassword, password);
      navigate('/app', { replace: true });
    } catch (err) {
      setFieldErrors(extractFieldErrors(err));
      setError(extractErrorMessage(err, 'Unable to update password.'));
    }
  }

  return (
    <Card>
      <div className="auth-page__header">
        <h2>Set a new password</h2>
        <p>
          Welcome{auth.user?.first_name ? `, ${auth.user.first_name}` : ''}. Replace your temporary
          invite password before continuing.
        </p>
      </div>
      <form className="auth-form" onSubmit={onSubmit}>
        {error ? (
          <div className="auth-alert auth-alert--error" role="alert">
            {error}
          </div>
        ) : null}
        <PasswordInput
          id="current-password"
          label="Temporary password"
          autoComplete="current-password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          error={fieldErrors.current_password}
          required
        />
        <PasswordInput
          id="new-password"
          label="New password"
          autoComplete="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={fieldErrors.password}
          required
        />
        <PasswordInput
          id="confirm-password"
          label="Confirm new password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          required
        />
        <Button type="submit" fullWidth loading={auth.loading}>
          Save password & continue
        </Button>
      </form>
      <style>{`.auth-form{display:flex;flex-direction:column;gap:1rem}`}</style>
    </Card>
  );
}
