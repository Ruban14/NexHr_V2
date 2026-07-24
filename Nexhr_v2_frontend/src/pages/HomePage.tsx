import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { organizationApi } from '../api/auth';
import { useAuth } from '../auth/AuthContext';
import { tokenStorage } from '../auth/tokenStorage';
import { BrandMark } from '../components/BrandMark';
import { Button } from '../components/Button';
import './HomePage.css';

export function HomePage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = tokenStorage.getAccessToken();
    if (!token) {
      navigate('/auth/login', { replace: true });
      return;
    }

    let cancelled = false;
    async function check() {
      try {
        const status = await organizationApi.getSetupStatus(token!);
        if (!cancelled && status.needs_setup) {
          navigate('/organizations/create', { replace: true });
          return;
        }
      } catch {
        // stay on home
      } finally {
        if (!cancelled) setChecking(false);
      }
    }
    void check();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  if (checking) {
    return <div className="boot-screen">Loading workspace…</div>;
  }

  return (
    <div className="home">
      <header className="home__header">
        <BrandMark size="sm" />
        <Button
          variant="secondary"
          loading={auth.loading}
          onClick={async () => {
            await auth.logout();
            navigate('/auth/login');
          }}
        >
          Sign out
        </Button>
      </header>
      <main className="home__main">
        <h1>Welcome, {auth.displayName}</h1>
        <p>You are signed in to NexHr.</p>
      </main>
    </div>
  );
}
