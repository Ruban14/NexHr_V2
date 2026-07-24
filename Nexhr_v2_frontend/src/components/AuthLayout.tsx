import { Outlet, useLocation } from 'react-router-dom';
import { BrandMark } from './BrandMark';
import './AuthLayout.css';

export function AuthLayout() {
  const location = useLocation();
  const isLoginLike =
    location.pathname.startsWith('/auth/login') ||
    location.pathname.startsWith('/auth/forgot-password') ||
    location.pathname.startsWith('/auth/reset-password');
  const isWide = location.pathname.startsWith('/organizations');

  return (
    <div
      className={[
        'auth-layout',
        isLoginLike ? 'auth-layout--login' : '',
        isWide ? 'auth-layout--wide' : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {!isWide ? (
        <div className="auth-layout__panel auth-layout__panel--brand">
          {isLoginLike ? (
            <div className="auth-layout__ambiance" aria-hidden="true">
              <span className="auth-layout__orb auth-layout__orb--a" />
              <span className="auth-layout__orb auth-layout__orb--b" />
              <span className="auth-layout__orb auth-layout__orb--c" />
              <span className="auth-layout__sheen" />
            </div>
          ) : null}

          <div className="auth-layout__brand">
            <BrandMark size="lg" tone={isLoginLike ? 'inverse' : 'default'} />
            <h1 className="auth-layout__headline">Modern HR operations for every industry.</h1>
            <p className="auth-layout__copy">
              Secure access to your NexHr workspace with enterprise-grade authentication and a
              polished experience built for teams that scale.
            </p>

            {isLoginLike ? (
              <>
                <ul className="auth-layout__perks" aria-label="Why NexHr">
                  <li>
                    <span className="auth-layout__perk-icon" aria-hidden="true">
                      ✓
                    </span>
                    <div>
                      <strong>One workspace</strong>
                      <span>People, identity, and org access in one place</span>
                    </div>
                  </li>
                  <li>
                    <span className="auth-layout__perk-icon" aria-hidden="true">
                      ✓
                    </span>
                    <div>
                      <strong>Secure sign-in</strong>
                      <span>Protected sessions with organization context</span>
                    </div>
                  </li>
                  <li>
                    <span className="auth-layout__perk-icon" aria-hidden="true">
                      ✓
                    </span>
                    <div>
                      <strong>Built to scale</strong>
                      <span>From first hire through full lifecycle management</span>
                    </div>
                  </li>
                </ul>
                <p className="auth-layout__org-note">
                  Sign in with the email you used when your organization was set up.
                </p>
              </>
            ) : (
              <p className="auth-layout__org-note">Create your account to get started with NexHr.</p>
            )}
          </div>
        </div>
      ) : null}

      <div className="auth-layout__panel auth-layout__panel--form">
        <div className="auth-layout__form-shell">
          <div className="auth-layout__mobile-brand">
            <BrandMark size="sm" showWordmark />
          </div>
          <div className="auth-layout__outlet">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
