import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { SETUP_NAV } from '../../masters/masterConfig';
import { getInitial, hasLogoUrl } from '../../utils/initials';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { SetupNavIcon } from './SetupIcons';
import './OrganizationSetupPage.css';

export function OrganizationSetupLayout() {
  const { currentBranch, organization } = useWorkspace();
  const [logoBroken, setLogoBroken] = useState(false);

  useEffect(() => {
    setLogoBroken(false);
  }, [organization?.id, organization?.logo]);

  const orgName = organization?.display_name || organization?.legal_name || 'Organization';
  const initial = getInitial(organization?.display_name, organization?.legal_name, 'N');
  const logo = organization?.logo?.trim() || '';
  const showLogo = hasLogoUrl(logo) && !logoBroken;

  return (
    <div className="org-setup">
      <header className="org-setup__hero">
        <div className="org-setup__hero-brand">
          {showLogo ? (
            <img
              key={organization?.id}
              src={logo}
              alt=""
              className="org-setup__hero-logo"
              onError={() => setLogoBroken(true)}
            />
          ) : (
            <span className="org-setup__hero-fallback" aria-hidden>
              {initial}
            </span>
          )}
          <div className="org-setup__hero-copy">
            <p className="org-setup__eyebrow">Organization setup</p>
            <h1>{orgName}</h1>
            <p>
              Configure masters for{' '}
              <strong>{currentBranch?.branch_name || 'the selected branch'}</strong>
              {currentBranch?.is_headquarters ? ' (HQ)' : ''}.
            </p>
          </div>
        </div>
        <div className="org-setup__hero-actions">
          {organization?.can_edit ? (
            <Link to="/app/organization" className="org-setup__hero-link">
              Edit organization
            </Link>
          ) : null}
          <div className="org-setup__hero-chip">
            <span>Branch</span>
            <strong>{currentBranch?.branch_name || '—'}</strong>
          </div>
        </div>
      </header>

      <div className="org-setup__body">
        <aside className="org-setup__nav" aria-label="Organization setup">
          <p className="org-setup__nav-label">Masters</p>
          <nav>
            {SETUP_NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => `org-setup__link ${isActive ? 'is-active' : ''}`}
              >
                <span className="org-setup__link-icon">
                  <SetupNavIcon name={item.icon} />
                </span>
                <span className="org-setup__link-copy">
                  <strong>{item.label}</strong>
                  <em>{item.description}</em>
                </span>
              </NavLink>
            ))}
          </nav>
        </aside>

        <div className="org-setup__content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
