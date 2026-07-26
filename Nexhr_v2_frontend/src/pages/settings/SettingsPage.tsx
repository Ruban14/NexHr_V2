import { Link } from 'react-router-dom';
import { useTheme, type ThemeMode } from '../../theme/ThemeContext';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import '../organization-edit/OrganizationEditPage.css';

const THEME_OPTIONS: { value: ThemeMode; label: string; hint: string }[] = [
  { value: 'light', label: 'Light', hint: 'Bright stone surfaces' },
  { value: 'dark', label: 'Dark', hint: 'Deep ink workspace' },
  { value: 'system', label: 'System', hint: 'Follow device setting' },
];

export function SettingsPage() {
  const workspace = useWorkspace();
  const theme = useTheme();

  return (
    <div className="settings-page">
      <div className="settings-page__head">
        <div>
          <p className="settings-page__eyebrow">Account</p>
          <h1>Settings</h1>
          <p>Theme, profile shortcuts, and workspace preferences.</p>
        </div>
        <Link to="/app" className="settings-page__back">
          Back
        </Link>
      </div>

      <section className="theme-picker" aria-label="Appearance">
        <div className="theme-picker__intro">
          <strong>Appearance</strong>
          <span>Switch light, dark, or match your system. Preference is saved on this device.</span>
        </div>
        <div className="theme-picker__options" role="radiogroup" aria-label="Theme mode">
          {THEME_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              role="radio"
              aria-checked={theme.mode === option.value}
              className={`theme-picker__option ${theme.mode === option.value ? 'is-active' : ''}`}
              onClick={() => theme.setMode(option.value)}
            >
              <span className={`theme-picker__swatch theme-picker__swatch--${option.value}`} aria-hidden />
              <span>
                <strong>{option.label}</strong>
                <em>{option.hint}</em>
              </span>
            </button>
          ))}
        </div>
      </section>

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
