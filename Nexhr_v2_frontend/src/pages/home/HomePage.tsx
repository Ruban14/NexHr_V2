import { useNavigate } from 'react-router-dom';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { Button } from '../../components/Button';
import './HomePage.css';

const WORKSPACE_AREAS = [
  {
    title: 'People',
    description: 'Employee profiles, roles, and org structure.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M16 11a3 3 0 1 0-3-3 3 3 0 0 0 3 3ZM8 11a3 3 0 1 0-3-3 3 3 0 0 0 3 3ZM8.2 13.5c-2.4 0-7.2 1.2-7.2 3.6V19h8.4M15.8 13.5c.4 0 .8 0 1.2.05 2.35.35 6 1.5 6 3.55V19h-6"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    title: 'Attendance',
    description: 'Track presence, shifts, and time policies.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="8.25" stroke="currentColor" strokeWidth="1.6" />
        <path
          d="M12 8v4.2l2.8 1.6"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    title: 'Leave',
    description: 'Requests, balances, and approval workflows.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M7 4.5v2M17 4.5v2M4.5 9h15M6.5 7h11a2 2 0 0 1 2 2v8.5a2 2 0 0 1-2 2h-11a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    title: 'Payroll',
    description: 'Compensation cycles ready for your org.',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 3.75v16.5M16.5 8.25c0-1.66-2.01-3-4.5-3s-4.5 1.34-4.5 3 2.01 3 4.5 3 4.5 1.34 4.5 3-2.01 3-4.5 3-4.5-1.34-4.5-3"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
] as const;

export function HomePage() {
  const navigate = useNavigate();
  const workspace = useWorkspace();
  const displayName =
    workspace.profile?.display_name ||
    workspace.profile?.full_name ||
    workspace.organization?.display_name ||
    'there';
  const firstName = displayName.split(' ')[0] || displayName;

  return (
    <div className="home">
      <section className="home__hero">
        <div className="home__hero-brand" aria-hidden="true">
          {workspace.organization?.logo ? (
            <img src={workspace.organization.logo} alt="" className="home__hero-logo" />
          ) : (
            <span className="home__hero-badge">
              {(workspace.organization?.display_name?.[0] || 'N').toUpperCase()}
            </span>
          )}
          <span className="home__hero-word">
            {workspace.organization?.display_name || 'NexHr'}
          </span>
        </div>
        <h1>
          Welcome back,
          <span className="home__name"> {firstName}</span>
        </h1>
        <p className="home__lead">
          Your organization is ready. Run modern HR operations from one secure workspace built for
          teams that scale.
        </p>
        <div className="home__cta">
          <Button
            size="lg"
            onClick={() =>
              document
                .getElementById('workspace-areas')
                ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
            }
          >
            Explore workspace
          </Button>
          {workspace.organization?.can_edit ? (
            <Button size="lg" variant="secondary" onClick={() => navigate('/app/organization')}>
              Edit organization
            </Button>
          ) : null}
        </div>
      </section>

      <section className="home__areas" id="workspace-areas" aria-label="Workspace areas">
        <div className="home__areas-head">
          <h2>What you can run next</h2>
          <p>Core HR modules will light up here as you expand NexHr for your organization.</p>
        </div>
        <ul className="home__area-grid">
          {WORKSPACE_AREAS.map((area) => (
            <li key={area.title}>
              <button type="button" className="home__area" disabled title="Coming soon">
                <span className="home__area-icon">{area.icon}</span>
                <span className="home__area-copy">
                  <strong>{area.title}</strong>
                  <span>{area.description}</span>
                </span>
                <span className="home__area-badge">Soon</span>
              </button>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
