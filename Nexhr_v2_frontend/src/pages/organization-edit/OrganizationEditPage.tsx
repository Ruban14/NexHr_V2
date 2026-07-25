import {
  type ChangeEvent,
  type FormEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import { PageHeader } from '../../components/ui/PageHeader';
import { StatusBadge } from '../../components/ui/StatusBadge';
import type { IndustryType } from '../../types';
import { getInitial, hasLogoUrl } from '../../utils/initials';
import {
  clearLegacyOrgLogoCache,
  readImageFileAsDataUrl,
} from '../../workspace/orgLogoStorage';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './OrganizationEditPage.css';

const ORGANIZATION_SIZES = [
  { value: '1-10', label: '1–10 employees' },
  { value: '11-50', label: '11–50 employees' },
  { value: '51-200', label: '51–200 employees' },
  { value: '201-500', label: '201–500 employees' },
  { value: '500+', label: '500+ employees' },
];

type FieldProps = {
  label: string;
  required?: boolean;
  error?: string;
  hint?: string;
  children: ReactNode;
};

function Field({ label, required, error, hint, children }: FieldProps) {
  return (
    <label className="org-edit__field">
      <span className="org-edit__label">
        {label}
        {required ? <em>*</em> : null}
      </span>
      {children}
      {hint && !error ? <small className="org-edit__hint">{hint}</small> : null}
      {error ? <small className="org-edit__error">{error}</small> : null}
    </label>
  );
}

export function OrganizationEditPage() {
  const workspace = useWorkspace();
  const org = workspace.organization;
  const currentBranch = workspace.currentBranch;
  const token = tokenStorage.getAccessToken();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [industries, setIndustries] = useState<IndustryType[]>([]);
  const [legalName, setLegalName] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [industryTypeId, setIndustryTypeId] = useState('');
  const [organizationSize, setOrganizationSize] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [website, setWebsite] = useState('');
  const [logo, setLogo] = useState('');
  const [country, setCountry] = useState('');
  const [state, setStateValue] = useState('');
  const [city, setCity] = useState('');
  const [timezone, setTimezone] = useState('Asia/Kolkata');
  const [currency, setCurrency] = useState('INR');
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [logoBroken, setLogoBroken] = useState(false);

  useEffect(() => {
    if (!org) return;
    clearLegacyOrgLogoCache(org.id);
    const resolved = org.logo?.trim() || '';
    setLegalName(org.legal_name);
    setDisplayName(org.display_name);
    setIndustryTypeId(org.industry_type_id ?? '');
    setOrganizationSize(org.organization_size);
    setEmail(org.email);
    setPhone(org.phone);
    setWebsite(org.website);
    setLogo(resolved);
    setCountry(org.country);
    setStateValue(org.state);
    setCity(org.city);
    setTimezone(org.timezone || 'Asia/Kolkata');
    setCurrency(org.currency || 'INR');
    setLogoBroken(false);
    // Hydrate once per organization — avoid wiping in-progress edits when logo preview updates.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [org?.id]);

  useEffect(() => {
    setLogoBroken(false);
  }, [logo]);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    async function load() {
      try {
        const list = await organizationApi.listIndustryTypes(token!);
        if (!cancelled) setIndustries(list);
      } catch {
        // keep empty list
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const industryName = useMemo(
    () => industries.find((item) => item.id === industryTypeId)?.name || org?.industry_type_name || '—',
    [industries, industryTypeId, org?.industry_type_name],
  );

  const locationLabel = useMemo(() => {
    const parts = [city, state, country].map((part) => part.trim()).filter(Boolean);
    return parts.length ? parts.join(', ') : 'Location not set';
  }, [city, state, country]);

  const previewInitial = getInitial(displayName, legalName, org?.display_name, org?.legal_name, 'N');
  const showLogo = hasLogoUrl(logo) && !logoBroken;

  if (!org) {
    return <div className="org-edit org-edit--empty">Organization not found.</div>;
  }

  if (!org.can_edit) {
    return (
      <div className="org-edit org-edit--locked">
        <PageHeader
          title="Organization details"
          description="Only the organization owner can edit these details."
        />
        <div className="org-edit__locked-card">
          <p>You can still configure masters for your branch from Organization Setup.</p>
          <div className="org-edit__locked-actions">
            <Link to="/app/setup">Go to setup</Link>
            <Link to="/app">Back to workspace</Link>
          </div>
        </div>
      </div>
    );
  }

  async function persistLogo(nextLogo: string, successMessage: string) {
    if (!token || !org) return;
    const updated = await organizationApi.updateCurrent(token, { logo: nextLogo });
    clearLegacyOrgLogoCache(org.id);
    setLogo(updated.logo || '');
    setLogoBroken(false);
    workspace.setOrganization(updated);
    setMessage(successMessage);
  }

  async function onUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file || !org || !token) return;
    setUploading(true);
    setError(null);
    setMessage(null);
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next.logo;
      return next;
    });
    try {
      const dataUrl = await readImageFileAsDataUrl(file);
      await persistLogo(dataUrl, 'Logo uploaded and saved.');
    } catch (err) {
      setFieldErrors(extractFieldErrors(err));
      setError(extractErrorMessage(err, 'Unable to upload logo.'));
    } finally {
      setUploading(false);
    }
  }

  async function clearLogo() {
    if (!org || !token) return;
    setUploading(true);
    setError(null);
    setMessage(null);
    try {
      await persistLogo('', 'Logo removed.');
    } catch (err) {
      setFieldErrors(extractFieldErrors(err));
      setError(extractErrorMessage(err, 'Unable to remove logo.'));
    } finally {
      setUploading(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token || !org) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    setFieldErrors({});
    try {
      const updated = await organizationApi.updateCurrent(token, {
        legal_name: legalName.trim(),
        display_name: displayName.trim(),
        industry_type_id: industryTypeId || undefined,
        organization_size: organizationSize,
        email: email.trim(),
        phone: phone.trim(),
        website: website.trim(),
        logo: logo.trim(),
        country: country.trim(),
        state: state.trim(),
        city: city.trim(),
        timezone: timezone.trim(),
        currency: currency.trim().toUpperCase(),
      });
      clearLegacyOrgLogoCache(org.id);
      workspace.setOrganization(updated);
      setLogo(updated.logo || '');
      setMessage('Organization details saved.');
    } catch (err) {
      setFieldErrors(extractFieldErrors(err));
      setError(extractErrorMessage(err, 'Unable to update organization.'));
    } finally {
      setSaving(false);
    }
  }

  function resetForm() {
    if (!org) return;
    const resolved = org.logo?.trim() || '';
    setLegalName(org.legal_name);
    setDisplayName(org.display_name);
    setIndustryTypeId(org.industry_type_id ?? '');
    setOrganizationSize(org.organization_size);
    setEmail(org.email);
    setPhone(org.phone);
    setWebsite(org.website);
    setLogo(resolved);
    setCountry(org.country);
    setStateValue(org.state);
    setCity(org.city);
    setTimezone(org.timezone || 'Asia/Kolkata');
    setCurrency(org.currency || 'INR');
    setMessage(null);
    setError(null);
    setFieldErrors({});
    setLogoBroken(false);
  }

  return (
    <div className="org-edit">
      <PageHeader
        title="Organization details"
        description="Manage how your company appears across NexHR — branding, contact info, and regional defaults."
        actions={
          <>
            <Link to="/app/setup" className="org-edit__ghost-link">
              Organization setup
            </Link>
            <Button type="submit" form="org-edit-form" loading={saving}>
              Save changes
            </Button>
          </>
        }
      />

      <section className="org-edit__hero" aria-label="Organization summary">
        <div className="org-edit__hero-brand">
          {showLogo ? (
            <img
              src={logo}
              alt=""
              className="org-edit__hero-logo"
              onError={() => setLogoBroken(true)}
            />
          ) : (
            <span className="org-edit__hero-fallback">{previewInitial}</span>
          )}
          <div className="org-edit__hero-copy">
            <div className="org-edit__hero-title-row">
              <h2>{displayName || legalName || 'Untitled organization'}</h2>
              <StatusBadge active={org.is_active} />
            </div>
            <p className="org-edit__hero-legal">{legalName || 'Legal name not set'}</p>
            <div className="org-edit__hero-meta">
              <span>{org.organization_code}</span>
              <span>{industryName}</span>
              <span>{locationLabel}</span>
              {currentBranch ? <span>{currentBranch.branch_name}</span> : null}
            </div>
          </div>
        </div>
        <dl className="org-edit__hero-stats">
          <div>
            <dt>Size</dt>
            <dd>{organizationSize || '—'}</dd>
          </div>
          <div>
            <dt>Timezone</dt>
            <dd>{timezone || '—'}</dd>
          </div>
          <div>
            <dt>Currency</dt>
            <dd>{currency || '—'}</dd>
          </div>
        </dl>
      </section>

      <form id="org-edit-form" className="org-edit__form" onSubmit={onSubmit} noValidate>
        {message ? (
          <div className="auth-alert auth-alert--success" role="status">
            {message}
          </div>
        ) : null}
        {error ? (
          <div className="auth-alert auth-alert--error" role="alert">
            {error}
          </div>
        ) : null}

        <div className="org-edit__layout">
          <aside className="org-edit__aside">
            <article className="org-edit__panel org-edit__panel--brand">
              <header className="org-edit__panel-head">
                <h3>Brand</h3>
                <p>Shown in the sidebar and workspace header.</p>
              </header>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp,image/gif"
                className="org-edit__file-input"
                onChange={(event) => void onUpload(event)}
              />

              <button
                type="button"
                className={`org-edit__brand-dropzone${showLogo ? ' org-edit__brand-dropzone--filled' : ''}`}
                disabled={uploading}
                onClick={() => fileInputRef.current?.click()}
                aria-label={showLogo ? 'Replace organization logo' : 'Upload organization logo'}
              >
                <span className="org-edit__brand-mark">
                  {showLogo ? (
                    <img
                      src={logo}
                      alt=""
                      className="org-edit__brand-mark-img"
                      onError={() => setLogoBroken(true)}
                    />
                  ) : (
                    <span className="org-edit__brand-mark-fallback" aria-hidden>
                      {previewInitial}
                    </span>
                  )}
                </span>
                <span className="org-edit__brand-dropzone-copy">
                  <strong>{showLogo ? 'Replace logo' : 'Upload logo'}</strong>
                  <span>PNG, JPG, or WebP · under 750 KB</span>
                </span>
                <span className="org-edit__brand-dropzone-icon" aria-hidden>
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 16V7M8.5 10.5 12 7l3.5 3.5" />
                    <path d="M5 18h14" />
                  </svg>
                </span>
              </button>

              {fieldErrors.logo ? (
                <small className="org-edit__error org-edit__brand-error">{fieldErrors.logo}</small>
              ) : null}

              {showLogo ? (
                <div className="org-edit__logo-actions">
                  <Button
                    type="button"
                    variant="secondary"
                    loading={uploading}
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Change
                  </Button>
                  <Button type="button" variant="ghost" loading={uploading} onClick={() => void clearLogo()}>
                    Remove
                  </Button>
                </div>
              ) : null}
            </article>

            <article className="org-edit__panel org-edit__panel--tips">
              <h3>Quick links</h3>
              <Link to="/app/setup/departments" className="org-edit__tip-link">
                <strong>Departments</strong>
                <span>Structure your branch teams</span>
              </Link>
              <Link to="/app/setup/designations" className="org-edit__tip-link">
                <strong>Designations</strong>
                <span>Build the reporting hierarchy</span>
              </Link>
              <Link to="/app/setup/access-types" className="org-edit__tip-link">
                <strong>Access types</strong>
                <span>Define Admin, Manager, Employee roles</span>
              </Link>
            </article>
          </aside>

          <div className="org-edit__main">
            <article className="org-edit__panel">
              <header className="org-edit__panel-head">
                <h3>Company profile</h3>
                <p>Core identity used across payroll, documents, and invites.</p>
              </header>
              <div className="org-edit__grid org-edit__grid--2">
                <Field label="Legal name" required error={fieldErrors.legal_name}>
                  <input
                    value={legalName}
                    onChange={(e) => setLegalName(e.target.value)}
                    required
                  />
                </Field>
                <Field label="Display name" hint="Shown in the app header">
                  <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
                </Field>
                <Field label="Industry">
                  <select value={industryTypeId} onChange={(e) => setIndustryTypeId(e.target.value)}>
                    <option value="">Select industry</option>
                    {industries.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Organization size">
                  <select
                    value={organizationSize}
                    onChange={(e) => setOrganizationSize(e.target.value)}
                  >
                    <option value="">Select size</option>
                    {ORGANIZATION_SIZES.map((size) => (
                      <option key={size.value} value={size.value}>
                        {size.label}
                      </option>
                    ))}
                  </select>
                </Field>
              </div>
            </article>

            <article className="org-edit__panel">
              <header className="org-edit__panel-head">
                <h3>Contact</h3>
                <p>Primary channels for HR communication and system notices.</p>
              </header>
              <div className="org-edit__grid org-edit__grid--2">
                <Field label="Email" error={fieldErrors.email}>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="hr@company.com"
                  />
                </Field>
                <Field label="Phone" error={fieldErrors.phone}>
                  <input value={phone} onChange={(e) => setPhone(e.target.value)} />
                </Field>
                <Field label="Website" error={fieldErrors.website}>
                  <input
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://company.com"
                  />
                </Field>
              </div>
            </article>

            <article className="org-edit__panel">
              <header className="org-edit__panel-head">
                <h3>Location & regional</h3>
                <p>Defaults used for attendance, leave calendars, and currency display.</p>
              </header>
              <div className="org-edit__grid org-edit__grid--3">
                <Field label="Country">
                  <input value={country} onChange={(e) => setCountry(e.target.value)} />
                </Field>
                <Field label="State">
                  <input value={state} onChange={(e) => setStateValue(e.target.value)} />
                </Field>
                <Field label="City">
                  <input value={city} onChange={(e) => setCity(e.target.value)} />
                </Field>
              </div>
              <div className="org-edit__grid org-edit__grid--2">
                <Field label="Timezone" hint="e.g. Asia/Kolkata">
                  <input value={timezone} onChange={(e) => setTimezone(e.target.value)} />
                </Field>
                <Field label="Currency" error={fieldErrors.currency} hint="3-letter code">
                  <input
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    maxLength={3}
                  />
                </Field>
              </div>
            </article>
          </div>
        </div>

        <footer className="org-edit__footer">
          <p>Save to update organization records. Logos are stored on the server for now.</p>
          <div className="org-edit__footer-actions">
            <Button type="button" variant="ghost" disabled={saving} onClick={resetForm}>
              Reset
            </Button>
            <Button type="submit" size="lg" loading={saving}>
              Save changes
            </Button>
          </div>
        </footer>
      </form>
    </div>
  );
}
