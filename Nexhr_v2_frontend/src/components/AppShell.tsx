import { useEffect, useRef, useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useWorkspace } from '../workspace/WorkspaceContext';
import './AppShell.css';

export function AppShell() {
  const auth = useAuth();
  const workspace = useWorkspace();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setMenuOpen(false);
    }
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, []);

  if (workspace.loading) {
    return <div className="boot-screen">Loading workspace…</div>;
  }

  const org = workspace.organization;
  const profile = workspace.profile;
  const displayName =
    profile?.display_name ||
    profile?.full_name ||
    auth.displayName ||
    auth.user?.email ||
    'User';
  const initial = (displayName[0] || 'U').toUpperCase();
  const orgInitial = (org?.display_name?.[0] || 'N').toUpperCase();

  return (
    <div className="app-shell">
      <header className="app-shell__header">
        <Link to="/app" className="app-shell__org" title={org?.display_name || 'Organization'}>
          {org?.logo ? (
            <img src={org.logo} alt="" className="app-shell__org-logo" />
          ) : (
            <span className="app-shell__org-fallback" aria-hidden="true">
              {orgInitial}
            </span>
          )}
          <div className="app-shell__org-meta">
            <strong>{org?.display_name || 'NexHr'}</strong>
            <span>{org?.organization_code || 'Enterprise HR Platform'}</span>
          </div>
        </Link>

        <div className="app-shell__actions">
          <div className="app-shell__menu" ref={menuRef}>
            <button
              type="button"
              className="app-shell__avatar-btn"
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              {profile?.profile_photo ? (
                <img src={profile.profile_photo} alt="" className="app-shell__avatar-img" />
              ) : (
                <span className="app-shell__avatar-fallback" aria-hidden="true">
                  {initial}
                </span>
              )}
              <span className="app-shell__avatar-copy">
                <strong>{displayName}</strong>
                <span>{auth.user?.email}</span>
              </span>
              <span className="app-shell__caret" aria-hidden="true">
                ▾
              </span>
            </button>

            {menuOpen ? (
              <div className="app-shell__dropdown" role="menu">
                <div className="app-shell__dropdown-head">
                  <strong>{displayName}</strong>
                  <span>{auth.user?.email}</span>
                </div>
                <Link
                  to="/app/profile"
                  role="menuitem"
                  className="app-shell__dropdown-item"
                  onClick={() => setMenuOpen(false)}
                >
                  Edit profile
                </Link>
                {org?.can_edit ? (
                  <Link
                    to="/app/organization"
                    role="menuitem"
                    className="app-shell__dropdown-item"
                    onClick={() => setMenuOpen(false)}
                  >
                    Edit organization
                  </Link>
                ) : null}
                <Link
                  to="/app/settings"
                  role="menuitem"
                  className="app-shell__dropdown-item"
                  onClick={() => setMenuOpen(false)}
                >
                  Settings
                </Link>
                <button
                  type="button"
                  role="menuitem"
                  className="app-shell__dropdown-item app-shell__dropdown-item--danger"
                  onClick={async () => {
                    setMenuOpen(false);
                    await auth.logout();
                    navigate('/auth/login');
                  }}
                >
                  Logout
                </button>
              </div>
            ) : null}
          </div>
        </div>
      </header>

      <div className="app-shell__body">
        <Outlet />
      </div>
    </div>
  );
}
