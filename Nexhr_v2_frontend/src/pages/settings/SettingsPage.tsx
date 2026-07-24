import { Link } from 'react-router-dom';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import '../organization-edit/OrganizationEditPage.css';

export function SettingsPage() {
  const workspace = useWorkspace();

  return (
    <div className="settings-page">
      <div className="settings-page__head">
        <div>
          <p className="settings-page__eyebrow">Account</p>
          <h1>Settings</h1>
          <p>Manage your workspace preferences and account details.</p>
        </div>
        <Link to="/app" className="settings-page__back">
          Back
        </Link>
      </div>

      <div className="settings-links">
        <Link to="/app/profile" className="settings-link">
          <strong>Edit profile</strong>
          <span>Name, photo, contact, and personal details</span>
        </Link>
        {workspace.organization?.can_edit ? (
          <Link to="/app/organization" className="settings-link">
            <strong>Edit organization</strong>
            <span>Company details, logo, and workspace identity</span>
          </Link>
        ) : null}
      </div>
    </div>
  );
}
