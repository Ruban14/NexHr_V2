import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { getInitial, hasLogoUrl } from '../utils/initials';
import { useWorkspace } from '../workspace/WorkspaceContext';
import { BranchSwitcher } from './BranchSwitcher';
import './AppShell.css';

function resolvePageTitle(pathname: string): string {
  if (pathname.includes('/setup')) return 'Organization Setup';
  if (pathname.includes('/organization')) return 'Organization';
  if (pathname.includes('/profile')) return 'User Profile';
  if (pathname.includes('/settings')) return 'Settings';
  return 'Home';
}

export function AppShell() {
  const auth = useAuth();
  const workspace = useWorkspace();
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
  const roleLabel =
    profile?.access_type_name ||
    (profile?.employee_code ? `Emp ${profile.employee_code}` : 'Member');
  const initial = getInitial(displayName, auth.user?.email, 'U');
  const orgInitial = getInitial(org?.display_name, org?.legal_name, 'N');
  const resolvedLogo = org?.logo?.trim() || '';
  const showOrgLogo = hasLogoUrl(resolvedLogo) && !orgLogoBroken;
  const pageTitle = resolvePageTitle(location.pathname);

  return (
    <div className={`page-wrapper ${sidebarOpen ? 'sidebar-open' : ''}`}>
      <div className="sidebar-wrapper">
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
            <span className="logo-text">{org?.display_name || org?.legal_name || 'NexHr'}</span>
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

        <nav className="sidebar-nav custom-scrollbar" aria-label="Sidebar">
          <div className="sidebar-section">
            <p className="sidebar-title">Workspace</p>
            <ul className="sidebar-links">
              <li>
                <NavLink to="/app" end className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
                  Home
                </NavLink>
              </li>
              <li>
                <NavLink
                  to="/app/setup"
                  className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                >
                  Organization Setup
                </NavLink>
              </li>
              {org?.can_edit ? (
                <li>
                  <NavLink
                    to="/app/organization"
                    className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
                  >
                    Organization Details
                  </NavLink>
                </li>
              ) : null}
            </ul>
          </div>
        </nav>
      </div>

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
              <input type="search" placeholder="Search anything..." aria-label="Search" />
            </div>
          </div>

          <div className="header-right">
            <BranchSwitcher />

            <button type="button" className="header-icon-btn" title="Notifications" aria-label="Notifications">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8">
                <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2c0 .5-.2 1-.6 1.4L4 17h5" />
                <path d="M9.5 17a2.5 2.5 0 0 0 5 0" />
              </svg>
            </button>

            <div className="profile-nav" ref={menuRef}>
              <button
                type="button"
                className="profile-nav__btn"
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
              </button>

              {menuOpen ? (
                <div className="profile-dropdown" role="menu">
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
                    Settings
                  </Link>
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
                    Log Out
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </header>

        <div className="page-body">
          <div className="page-title">
            <h3>{pageTitle}</h3>
            <ol className="breadcrumb">
              <li>
                <Link to="/app">Home</Link>
              </li>
              <li>/</li>
              <li className="active">{pageTitle}</li>
            </ol>
          </div>
          {workspace.error ? <div className="auth-alert auth-alert--error">{workspace.error}</div> : null}
          <Outlet />
        </div>
      </div>
    </div>
  );
}
