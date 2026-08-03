import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useTheme } from '../theme/ThemeContext';
import { getInitial, hasLogoUrl } from '../utils/initials';
import { useWorkspace } from '../workspace/WorkspaceContext';
import { BranchSwitcher } from './BranchSwitcher';
import './AppShell.css';

function resolvePageTitle(pathname: string): string {
  if (pathname.includes('/employees/')) return 'Employee profile';
  if (pathname.includes('/employees')) return 'Employees';
  if (pathname.includes('/leave-approvals')) return 'Leave approvals';
  if (pathname.includes('/attendance-approvals')) return 'Attendance approvals';
  if (pathname.includes('/setup')) return 'Organization setup';
  if (pathname.includes('/organization')) return 'Organization';
  if (pathname.includes('/profile')) return 'Your profile';
  if (pathname.includes('/settings')) return 'Settings';
  return 'Home';
}

function NavIcon({ name }: { name: string }) {
  const props = {
    viewBox: '0 0 24 24',
    width: 18,
    height: 18,
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true as const,
  };
  switch (name) {
    case 'home':
      return (
        <svg {...props}>
          <path d="m3 11 9-8 9 8" />
          <path d="M5 10v10h14V10" />
        </svg>
      );
    case 'people':
      return (
        <svg {...props}>
          <circle cx="9" cy="8" r="3.2" />
          <path d="M3.5 19a5.5 5.5 0 0 1 11 0" />
          <circle cx="17" cy="9" r="2.4" />
          <path d="M20.5 19a4.2 4.2 0 0 0-4-4" />
        </svg>
      );
    case 'leave':
      return (
        <svg {...props}>
          <rect x="4" y="5" width="16" height="15" rx="2" />
          <path d="M8 3v4M16 3v4M4 10h16" />
          <path d="m9 15 2 2 4-4" />
        </svg>
      );
    case 'attendance':
      return (
        <svg {...props}>
          <circle cx="12" cy="12" r="8" />
          <path d="M12 8v4l2.5 1.5" />
        </svg>
      );
    case 'setup':
      return (
        <svg {...props}>
          <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
          <circle cx="12" cy="12" r="3.2" />
        </svg>
      );
    case 'org':
      return (
        <svg {...props}>
          <path d="M4 20V8l8-4 8 4v12" />
          <path d="M9 20v-6h6v6" />
        </svg>
      );
    default:
      return null;
  }
}

function ThemeGlyph({ mode }: { mode: string }) {
  const props = {
    viewBox: '0 0 24 24',
    width: 18,
    height: 18,
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true as const,
  };
  if (mode === 'dark') {
    return (
      <svg {...props}>
        <path d="M21 14.5A8.5 8.5 0 0 1 9.5 3 7 7 0 1 0 21 14.5z" />
      </svg>
    );
  }
  if (mode === 'system') {
    return (
      <svg {...props}>
        <rect x="3" y="4" width="18" height="14" rx="2" />
        <path d="M8 21h8M12 18v3" />
      </svg>
    );
  }
  return (
    <svg {...props}>
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
    </svg>
  );
}

export function AppShell() {
  const auth = useAuth();
  const workspace = useWorkspace();
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [orgLogoBroken, setOrgLogoBroken] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onPointerDown(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setMenuOpen(false);
        setSidebarOpen(false);
      }
    }
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('keydown', onKeyDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('keydown', onKeyDown);
    };
  }, []);

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    setOrgLogoBroken(false);
  }, [workspace.organization?.logo, workspace.organization?.id]);

  if (workspace.loading && !workspace.organization) {
    return <div className="boot-screen">Preparing your workspace…</div>;
  }

  const org = workspace.organization;
  const profile = workspace.profile;
  const displayName =
    profile?.display_name ||
    profile?.full_name ||
    auth.displayName ||
    auth.user?.email ||
    'User';
  const roleLabel =
    profile?.access_type_name ||
    (profile?.employee_code ? `Emp ${profile.employee_code}` : 'Member');
  const initial = getInitial(displayName, auth.user?.email, 'U');
  const orgInitial = getInitial(org?.display_name, org?.legal_name, 'N');
  const resolvedLogo = org?.logo?.trim() || '';
  const showOrgLogo = hasLogoUrl(resolvedLogo) && !orgLogoBroken;
  const pageTitle = resolvePageTitle(location.pathname);
  const themeLabel =
    theme.mode === 'system' ? 'System theme' : theme.mode === 'dark' ? 'Dark theme' : 'Light theme';

  const navItems = [
    { to: '/app', end: true, label: 'Home', icon: 'home' },
    { to: '/app/employees', end: false, label: 'Employees', icon: 'people' },
    { to: '/app/attendance-approvals', end: false, label: 'Attendance approvals', icon: 'attendance' },
    { to: '/app/leave-approvals', end: false, label: 'Leave approvals', icon: 'leave' },
    { to: '/app/setup', end: false, label: 'Organization setup', icon: 'setup' },
    ...(org?.can_edit
      ? [{ to: '/app/organization', end: false, label: 'Organization', icon: 'org' }]
      : []),
  ];

  return (
    <div className={`page-wrapper ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <aside className="sidebar-wrapper" aria-label="Main navigation">
        <div className="logo-wrapper">
          <Link to="/app" className="logo-link">
            {showOrgLogo ? (
              <img
                key={`${org?.id}-${resolvedLogo.slice(0, 48)}`}
                src={resolvedLogo}
                alt=""
                className="logo-img"
                onError={() => setOrgLogoBroken(true)}
              />
            ) : (
              <span className="logo-mark" aria-hidden>
                {orgInitial}
              </span>
            )}
            <span className="logo-copy">
              <span className="logo-text">{org?.display_name || org?.legal_name || 'NexHr'}</span>
              <span className="logo-sub">People workspace</span>
            </span>
          </Link>
          <button
            type="button"
            className="sidebar-toggle"
            aria-label="Toggle sidebar"
            onClick={() => setSidebarOpen((v) => !v)}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 7h16M4 12h16M4 17h16" />
            </svg>
          </button>
        </div>

        <nav className="sidebar-nav custom-scrollbar">
          <div className="sidebar-section">
            <p className="sidebar-title">Navigate</p>
            <ul className="sidebar-links">
              {navItems.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                  >
                    <span className="sidebar-link__icon">
                      <NavIcon name={item.icon} />
                    </span>
                    <span>{item.label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>

          <div className="sidebar-footer">
            <p>Crafted for first-day clarity</p>
            <span>Lifecycle · Masters · Teams</span>
          </div>
        </nav>
      </aside>

      {sidebarOpen ? (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Close sidebar"
          onClick={() => setSidebarOpen(false)}
        />
      ) : null}

      <div className="page-body-wrapper">
        <header className="page-header">
          <div className="header-left">
            <button
              type="button"
              className="mobile-toggle"
              aria-label="Open menu"
              onClick={() => setSidebarOpen(true)}
            >
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 7h16M4 12h16M4 17h16" />
              </svg>
            </button>
            <div className="header-search">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="7" />
                <path d="m20 20-3.5-3.5" />
              </svg>
              <input type="search" placeholder="Search people, masters…" aria-label="Search" />
              <kbd>⌘K</kbd>
            </div>
          </div>

          <div className="header-right">
            <BranchSwitcher />

            <button
              type="button"
              className="header-icon-btn"
              title={themeLabel}
              aria-label={themeLabel}
              onClick={theme.cycleMode}
            >
              <ThemeGlyph mode={theme.mode} />
            </button>

            <button type="button" className="header-icon-btn" title="Notifications" aria-label="Notifications">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2c0 .5-.2 1-.6 1.4L4 17h5" />
                <path d="M9.5 17a2.5 2.5 0 0 0 5 0" />
              </svg>
              <span className="header-badge header-badge--primary">3</span>
            </button>

            <div className="profile-nav" ref={menuRef}>
              <button
                type="button"
                className={`profile-nav__btn ${menuOpen ? 'is-open' : ''}`}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                onClick={() => setMenuOpen((open) => !open)}
              >
                {profile?.profile_photo ? (
                  <img src={profile.profile_photo} alt="" className="profile-nav__avatar" />
                ) : (
                  <span className="profile-nav__avatar profile-nav__avatar--fallback">{initial}</span>
                )}
                <span className="profile-nav__meta">
                  <strong>{displayName}</strong>
                  <span>{roleLabel}</span>
                </span>
                <svg
                  className="profile-nav__caret"
                  viewBox="0 0 24 24"
                  width="16"
                  height="16"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  aria-hidden
                >
                  <path d="m6 9 6 6 6-6" />
                </svg>
              </button>

              {menuOpen ? (
                <div className="profile-dropdown" role="menu">
                  <div className="profile-dropdown__head">
                    <strong>{displayName}</strong>
                    <span>{auth.user?.email}</span>
                  </div>
                  <div className="profile-dropdown__group">
                    <Link to="/app/profile" role="menuitem" onClick={() => setMenuOpen(false)}>
                      Edit profile
                    </Link>
                    <Link to="/app/setup" role="menuitem" onClick={() => setMenuOpen(false)}>
                      Organization setup
                    </Link>
                    {org?.can_edit ? (
                      <Link to="/app/organization" role="menuitem" onClick={() => setMenuOpen(false)}>
                        Edit organization
                      </Link>
                    ) : null}
                    <Link to="/app/settings" role="menuitem" onClick={() => setMenuOpen(false)}>
                      Settings & theme
                    </Link>
                  </div>
                  <button
                    type="button"
                    role="menuitem"
                    className="danger"
                    onClick={async () => {
                      setMenuOpen(false);
                      await auth.logout();
                      navigate('/auth/login');
                    }}
                  >
                    Log out
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <div className="page-body">
          <div className="page-title">
            <div>
              <p className="page-title__eyebrow">NexHr</p>
              <h3>{pageTitle}</h3>
            </div>
            <ol className="breadcrumb">
              <li>
                <Link to="/app">Home</Link>
              </li>
              <li aria-hidden>/</li>
              <li className="active">{pageTitle}</li>
            </ol>
          </div>
          {workspace.error ? <div className="auth-alert auth-alert--error">{workspace.error}</div> : null}
          <div className="page-outlet">
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  );
}
