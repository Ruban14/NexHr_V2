import { type FormEvent, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import type { IndustryType, OrganizationCreateResponse } from '../../types';
import './OrganizationCreatePage.css';

const STEP_LABELS = ['Industry', 'Organization', 'Done'];
const ORGANIZATION_SIZES = [
  { value: '1-10', label: '1–10 employees' },
  { value: '11-50', label: '11–50 employees' },
  { value: '51-200', label: '51–200 employees' },
  { value: '201-500', label: '201–500 employees' },
  { value: '500+', label: '500+ employees' },
];

const INDUSTRY_ICONS: Record<string, string> = {
  it: '💻',
  healthcare: '🏥',
  education: '🎓',
  finance: '🏦',
  manufacturing: '🏭',
  retail: '🛍️',
  hospitality: '🏨',
  construction: '🏗️',
  logistics: '🚚',
  others: '🏢',
};

export function OrganizationCreatePage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const token = tokenStorage.getAccessToken();

  const [step, setStep] = useState(0);
  const [industries, setIndustries] = useState<IndustryType[]>([]);
  const [loadingIndustries, setLoadingIndustries] = useState(true);
  const [selectedIndustry, setSelectedIndustry] = useState<IndustryType | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [created, setCreated] = useState<OrganizationCreateResponse | null>(null);

  const [legalName, setLegalName] = useState('');
  const [phone, setPhone] = useState('');
  const [website, setWebsite] = useState('');
  const [organizationSize, setOrganizationSize] = useState('');
  const [country, setCountry] = useState('');
  const [state, setStateValue] = useState('');
  const [city, setCity] = useState('');

  useEffect(() => {
    if (!token) {
      navigate('/auth/login', { replace: true });
      return;
    }

    let cancelled = false;
    async function load() {
      try {
        const status = await organizationApi.getSetupStatus(token!);
        if (!status.needs_setup) {
          navigate('/app', { replace: true });
          return;
        }
        const list = await organizationApi.listIndustryTypes(token!);
        if (!cancelled) setIndustries(list);
      } catch (err) {
        if (!cancelled) setSubmitError(extractErrorMessage(err, 'Unable to load setup.'));
      } finally {
        if (!cancelled) setLoadingIndustries(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [navigate, token]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token || !selectedIndustry) return;
    if (legalName.trim().length < 2 || phone.trim().length < 7) {
      setSubmitError('Organization name and a valid phone number are required.');
      return;
    }

    setSubmitting(true);
    setSubmitError('');
    setStep(2);

    try {
      const result = await organizationApi.createOrganization(token, {
        legal_name: legalName.trim(),
        display_name: legalName.trim(),
        industry_type_id: selectedIndustry.id,
        organization_size: organizationSize || undefined,
        email: auth.user?.email,
        phone: phone.trim(),
        website: website.trim() || undefined,
        country: country.trim() || undefined,
        state: state.trim() || undefined,
        city: city.trim() || undefined,
      });
      setCreated(result);
    } catch (err) {
      setSubmitError(extractErrorMessage(err, 'Unable to create organization.'));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="register-page">
      <div className="step-indicator">
        {STEP_LABELS.map((label, index) => (
          <div key={label} className="step-indicator__wrap">
            <button
              type="button"
              className={[
                'step-indicator__step',
                step === index ? 'is-active' : '',
                step > index ? 'is-done' : '',
              ]
                .filter(Boolean)
                .join(' ')}
              onClick={() => {
                if (index < step && step < 2) setStep(index);
              }}
              disabled={index >= step || step === 2}
            >
              <span className="step-indicator__circle">
                {step > index ? '✓' : index + 1}
              </span>
              <span className="step-indicator__label">{label}</span>
            </button>
            {index < STEP_LABELS.length - 1 ? (
              <span className={`step-indicator__line ${step > index ? 'is-done' : ''}`} />
            ) : null}
          </div>
        ))}
      </div>

      <div className="step-panel">
        {step === 0 ? (
          <div className="step-content">
            <div className="step-header">
              <h2>What industry are you in?</h2>
              <p>We&apos;ll tailor your NexHr experience to match your sector.</p>
            </div>
            {loadingIndustries ? (
              <p>Loading industries…</p>
            ) : (
              <div className="industry-grid">
                {industries.map((industry) => (
                  <button
                    key={industry.id}
                    type="button"
                    className={`industry-card ${selectedIndustry?.id === industry.id ? 'is-selected' : ''}`}
                    onClick={() => setSelectedIndustry(industry)}
                  >
                    <span className="industry-card__icon">
                      {INDUSTRY_ICONS[industry.code] ?? '🏢'}
                    </span>
                    <span className="industry-card__name">{industry.name}</span>
                  </button>
                ))}
              </div>
            )}
            <div className="step-actions">
              <Button
                size="lg"
                disabled={!selectedIndustry}
                onClick={() => setStep(1)}
              >
                Continue
              </Button>
            </div>
          </div>
        ) : null}

        {step === 1 ? (
          <div className="step-content">
            <div className="step-header">
              <h2>Tell us about your organization</h2>
              <p>Your verified account will be the organization admin.</p>
            </div>
            <div className="admin-banner">
              <strong>Default admin</strong>
              <span>{auth.user?.email} will be the Admin for this organization.</span>
            </div>
            <form className="details-form" onSubmit={onSubmit}>
              {submitError && step === 1 ? (
                <div className="auth-alert auth-alert--error">{submitError}</div>
              ) : null}
              <div className="form-row">
                <label className="field">
                  <span>Organization Name *</span>
                  <input
                    value={legalName}
                    onChange={(e) => setLegalName(e.target.value)}
                    placeholder="Acme Corp"
                    required
                  />
                </label>
                <label className="field">
                  <span>Work Email *</span>
                  <input value={auth.user?.email ?? ''} disabled />
                </label>
              </div>
              <div className="form-row">
                <label className="field">
                  <span>Phone *</span>
                  <input
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+91 98765 43210"
                    required
                  />
                </label>
                <label className="field">
                  <span>Website (optional)</span>
                  <input
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://company.com"
                  />
                </label>
              </div>
              <label className="field">
                <span>Organization size (optional)</span>
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
              <div className="step-actions step-actions--split">
                <Button type="button" variant="ghost" size="lg" onClick={() => setStep(0)}>
                  Back
                </Button>
                <Button type="submit" size="lg" loading={submitting}>
                  Create organization
                </Button>
              </div>
            </form>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="step-content step-content--center">
            {submitting ? (
              <div className="done-state">
                <h2>Setting up your organization…</h2>
                <p>Creating your admin profile and organization membership.</p>
              </div>
            ) : submitError ? (
              <div className="done-state">
                <h2>Setup failed</h2>
                <p>{submitError}</p>
                <div className="step-actions">
                  <Button variant="ghost" onClick={() => setStep(0)}>
                    Start over
                  </Button>
                  <Button onClick={() => setStep(1)}>Try again</Button>
                </div>
              </div>
            ) : created ? (
              <div className="done-state">
                <h2>You&apos;re all set!</h2>
                <p>
                  <strong>{created.organization.display_name}</strong> is ready. You&apos;re mapped
                  as Admin ({created.membership.employee_code}).
                </p>
                <Button size="lg" onClick={() => navigate('/app')}>
                  Go to dashboard
                </Button>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
