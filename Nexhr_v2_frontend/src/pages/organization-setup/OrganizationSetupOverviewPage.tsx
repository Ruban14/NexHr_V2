import { Link } from 'react-router-dom';
import { SETUP_MODULES } from '../../masters/masterConfig';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { SetupNavIcon } from './SetupIcons';

export function OrganizationSetupOverviewPage() {
  const { organization, currentBranch } = useWorkspace();

  return (
    <section className="setup-overview">
      <div className="setup-overview__intro">
        <h2>Build your organization foundation</h2>
        <p>
          Work through these masters in order. Everything here is scoped to the current branch
          {currentBranch ? (
            <>
              {' '}
              — <strong>{currentBranch.branch_name}</strong>
            </>
          ) : null}
          .
        </p>
      </div>

      <div className="setup-overview__context">
        <div>
          <span>Organization</span>
          <strong>{organization?.display_name || '—'}</strong>
        </div>
        <div>
          <span>Industry</span>
          <strong>{organization?.industry_type_name || '—'}</strong>
        </div>
        <div>
          <span>Branch</span>
          <strong>{currentBranch?.branch_name || '—'}</strong>
        </div>
        <div>
          <span>Code</span>
          <strong>{organization?.organization_code || '—'}</strong>
        </div>
      </div>

      <div className="setup-module-grid">
        {SETUP_MODULES.map((module) => (
          <Link key={module.to} to={module.to} className="setup-module-card">
            <div className="setup-module-card__top">
              <span className="setup-module-card__step">{module.step}</span>
              <span className="setup-module-card__icon">
                <SetupNavIcon name={module.icon} />
              </span>
            </div>
            <h3>{module.title}</h3>
            <p>{module.description}</p>
            <span className="setup-module-card__cta">Open {module.title}</span>
          </Link>
        ))}
      </div>

      {organization?.can_edit ? (
        <div className="setup-overview__footer">
          <div>
            <strong>Need to update company branding?</strong>
            <p>Legal name, logo, contact, and regional defaults live in organization details.</p>
          </div>
          <Link to="/app/organization" className="setup-overview__footer-link">
            Go to organization details
          </Link>
        </div>
      ) : null}
    </section>
  );
}
