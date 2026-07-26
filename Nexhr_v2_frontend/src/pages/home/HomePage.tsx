import { Link } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './HomePage.css';

const ACTIONS = [
  {
    to: '/app/employees',
    title: 'Employees',
    copy: 'Create drafts, move people through lifecycle, and keep history clean.',
    tone: 'teal',
  },
  {
    to: '/app/setup',
    title: 'Organization setup',
    copy: 'Departments, designations, holidays, shifts — the masters that power work.',
    tone: 'ink',
  },
  {
    to: '/app/profile',
    title: 'Your profile',
    copy: 'Photo, contact, and the details teammates see in the header menu.',
    tone: 'amber',
  },
] as const;

export function HomePage() {
  const auth = useAuth();
  const workspace = useWorkspace();
  const firstName =
    workspace.profile?.first_name ||
    auth.user?.first_name ||
    workspace.profile?.display_name?.split(' ')[0] ||
    'there';
  const orgName = workspace.organization?.display_name || workspace.organization?.legal_name || 'your company';
  const branch = workspace.currentBranch?.branch_name;

  return (
    <section className="home">
      <header className="home__hero">
        <div className="home__hero-copy">
          <p className="home__eyebrow">Welcome aboard</p>
          <h1>
            Hello, <em>{firstName}</em>
          </h1>
          <p className="home__lead">
            {orgName} is ready. Move people with confidence — from first draft to active teammate —
            in a workspace that stays calm and clear.
          </p>
          <div className="home__cta-row">
            <Link to="/app/employees" className="home__cta home__cta--primary">
              Open employees
            </Link>
            <Link to="/app/setup" className="home__cta home__cta--ghost">
              Configure setup
            </Link>
          </div>
        </div>
        <div className="home__hero-panel" aria-hidden>
          <div className="home__orb home__orb--a" />
          <div className="home__orb home__orb--b" />
          <div className="home__stat">
            <span>Branch</span>
            <strong>{branch || 'Headquarters'}</strong>
          </div>
          <div className="home__stat home__stat--delay">
            <span>Workspace</span>
            <strong>Live</strong>
          </div>
        </div>
      </header>

      <div className="home__grid">
        {ACTIONS.map((action, index) => (
          <Link
            key={action.to}
            to={action.to}
            className={`home__card home__card--${action.tone}`}
            style={{ animationDelay: `${0.08 + index * 0.06}s` }}
          >
            <span className="home__card-index">0{index + 1}</span>
            <h2>{action.title}</h2>
            <p>{action.copy}</p>
            <span className="home__card-go">Continue</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
