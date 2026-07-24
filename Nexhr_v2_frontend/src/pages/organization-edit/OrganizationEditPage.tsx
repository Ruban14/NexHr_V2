import { type FormEvent, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import type { IndustryType } from '../../types';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './OrganizationEditPage.css';

const ORGANIZATION_SIZES = [
  { value: '1-10', label: '1–10 employees' },
  { value: '11-50', label: '11–50 employees' },
  { value: '51-200', label: '51–200 employees' },
  { value: '201-500', label: '201–500 employees' },
  { value: '500+', label: '500+ employees' },
];

export function OrganizationEditPage() {
  const workspace = useWorkspace();
  const org = workspace.organization;
  const token = tokenStorage.getAccessToken();

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
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!org) return;
    setLegalName(org.legal_name);
    setDisplayName(org.display_name);
    setIndustryTypeId(org.industry_type_id ?? '');
    setOrganizationSize(org.organization_size);
    setEmail(org.email);
    setPhone(org.phone);
    setWebsite(org.website);
    setLogo(org.logo);
    setCountry(org.country);
    setStateValue(org.state);
    setCity(org.city);
    setTimezone(org.timezone || 'Asia/Kolkata');
    setCurrency(org.currency || 'INR');
  }, [org]);

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

  if (!org) {
    return <div className="settings-page">Organization not found.</div>;
  }

  if (!org.can_edit) {
    return (
      <div className="settings-page">
        <h1>Organization</h1>
        <p>Only the organization owner can edit these details.</p>
        <Link to="/app">Back to workspace</Link>
      </div>
    );
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
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
      workspace.setOrganization(updated);
      setMessage('Organization updated successfully.');
    } catch (err) {
      setFieldErrors(extractFieldErrors(err));
      setError(extractErrorMessage(err, 'Unable to update organization.'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="settings-page">
      <div className="settings-page__head">
        <div>
          <p className="settings-page__eyebrow">Organization</p>
          <h1>Edit organization</h1>
          <p>Update company details and the logo shown in your workspace header.</p>
        </div>
        <Link to="/app" className="settings-page__back">
          Back
        </Link>
      </div>

      <form className="settings-form" onSubmit={onSubmit} noValidate>
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

        <div className="settings-preview">
          {logo ? (
            <img src={logo} alt="" className="settings-preview__img" />
          ) : (
            <span className="settings-preview__fallback">
              {(displayName[0] || legalName[0] || 'N').toUpperCase()}
            </span>
          )}
          <div>
            <strong>Logo preview</strong>
            <span>Paste an image URL below. It appears in the top-left header.</span>
          </div>
        </div>

        <label className="field">
          <span>Logo URL</span>
          <input
            value={logo}
            onChange={(e) => setLogo(e.target.value)}
            placeholder="https://example.com/logo.png"
          />
          {fieldErrors.logo ? <em className="field-error">{fieldErrors.logo}</em> : null}
        </label>

        <div className="form-row">
          <label className="field">
            <span>Legal name *</span>
            <input value={legalName} onChange={(e) => setLegalName(e.target.value)} required />
            {fieldErrors.legal_name ? (
              <em className="field-error">{fieldErrors.legal_name}</em>
            ) : null}
          </label>
          <label className="field">
            <span>Display name</span>
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          </label>
        </div>

        <div className="form-row">
          <label className="field">
            <span>Industry</span>
            <select value={industryTypeId} onChange={(e) => setIndustryTypeId(e.target.value)}>
              <option value="">Select industry</option>
              {industries.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Organization size</span>
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
          </label>
        </div>

        <div className="form-row">
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="hr@company.com"
            />
          </label>
          <label className="field">
            <span>Phone</span>
            <input value={phone} onChange={(e) => setPhone(e.target.value)} />
            {fieldErrors.phone ? <em className="field-error">{fieldErrors.phone}</em> : null}
          </label>
        </div>

        <label className="field">
          <span>Website</span>
          <input
            value={website}
            onChange={(e) => setWebsite(e.target.value)}
            placeholder="https://company.com"
          />
        </label>

        <div className="form-row form-row--3">
          <label className="field">
            <span>Country</span>
            <input value={country} onChange={(e) => setCountry(e.target.value)} />
          </label>
          <label className="field">
            <span>State</span>
            <input value={state} onChange={(e) => setStateValue(e.target.value)} />
          </label>
          <label className="field">
            <span>City</span>
            <input value={city} onChange={(e) => setCity(e.target.value)} />
          </label>
        </div>

        <div className="form-row">
          <label className="field">
            <span>Timezone</span>
            <input value={timezone} onChange={(e) => setTimezone(e.target.value)} />
          </label>
          <label className="field">
            <span>Currency</span>
            <input
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              maxLength={3}
            />
          </label>
        </div>

        <div className="settings-form__actions">
          <Button type="submit" size="lg" loading={saving}>
            Save changes
          </Button>
        </div>
      </form>
    </div>
  );
}
