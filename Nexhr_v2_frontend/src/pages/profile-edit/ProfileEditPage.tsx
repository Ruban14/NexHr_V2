import { type FormEvent, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import '../organization-edit/OrganizationEditPage.css';

const GENDERS = [
  { value: '', label: 'Select gender' },
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
];

const BLOOD_GROUPS = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'unknown'];

export function ProfileEditPage() {
  const auth = useAuth();
  const workspace = useWorkspace();
  const profile = workspace.profile;
  const token = tokenStorage.getAccessToken();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [profilePhoto, setProfilePhoto] = useState('');
  const [mobileNumber, setMobileNumber] = useState('');
  const [alternateMobile, setAlternateMobile] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState('');
  const [bloodGroup, setBloodGroup] = useState('');
  const [country, setCountry] = useState('');
  const [state, setStateValue] = useState('');
  const [city, setCity] = useState('');
  const [addressLine1, setAddressLine1] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [motherLanguage, setMotherLanguage] = useState('');
  const [languagesKnown, setLanguagesKnown] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!profile) return;
    setFirstName(profile.first_name);
    setLastName(profile.last_name);
    setDisplayName(profile.display_name);
    setProfilePhoto(profile.profile_photo);
    setMobileNumber(profile.mobile_number);
    setAlternateMobile(profile.alternate_mobile);
    setDateOfBirth(profile.date_of_birth ?? '');
    setGender(profile.gender);
    setBloodGroup(profile.blood_group);
    setCountry(profile.country);
    setStateValue(profile.state);
    setCity(profile.city);
    setAddressLine1(profile.address_line1);
    setPostalCode(profile.postal_code);
    setMotherLanguage(profile.mother_language);
    setLanguagesKnown((profile.languages_known || []).join(', '));
  }, [profile]);

  if (!profile) {
    return <div className="settings-page">Profile not found.</div>;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    setFieldErrors({});
    try {
      const updated = await organizationApi.updateProfile(token, {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        display_name: displayName.trim(),
        profile_photo: profilePhoto.trim(),
        mobile_number: mobileNumber.trim(),
        alternate_mobile: alternateMobile.trim(),
        date_of_birth: dateOfBirth || null,
        gender,
        blood_group: bloodGroup,
        country: country.trim(),
        state: state.trim(),
        city: city.trim(),
        address_line1: addressLine1.trim(),
        postal_code: postalCode.trim(),
        mother_language: motherLanguage.trim(),
        languages_known: languagesKnown
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean),
      });
      workspace.setProfile(updated);
      await auth.refreshUser();
      setMessage('Profile updated successfully.');
    } catch (err) {
      setFieldErrors(extractFieldErrors(err));
      setError(extractErrorMessage(err, 'Unable to update profile.'));
    } finally {
      setSaving(false);
    }
  }

  const previewInitial = (displayName[0] || firstName[0] || 'U').toUpperCase();

  return (
    <div className="settings-page">
      <div className="settings-page__head">
        <div>
          <p className="settings-page__eyebrow">Account</p>
          <h1>Edit profile</h1>
          <p>Update your details and photo shown in the top-right menu.</p>
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
          {profilePhoto ? (
            <img src={profilePhoto} alt="" className="settings-preview__img settings-preview__img--round" />
          ) : (
            <span className="settings-preview__fallback settings-preview__fallback--round">
              {previewInitial}
            </span>
          )}
          <div>
            <strong>Photo preview</strong>
            <span>Paste an image URL. It appears in the header avatar menu.</span>
          </div>
        </div>

        <label className="field">
          <span>Profile photo URL</span>
          <input
            value={profilePhoto}
            onChange={(e) => setProfilePhoto(e.target.value)}
            placeholder="https://example.com/photo.jpg"
          />
          {fieldErrors.profile_photo ? (
            <em className="field-error">{fieldErrors.profile_photo}</em>
          ) : null}
        </label>

        <div className="form-row">
          <label className="field">
            <span>First name</span>
            <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
          </label>
          <label className="field">
            <span>Last name</span>
            <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
          </label>
        </div>

        <label className="field">
          <span>Display name</span>
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
        </label>

        <label className="field">
          <span>Email</span>
          <input value={profile.email} disabled />
        </label>

        <div className="form-row">
          <label className="field">
            <span>Mobile number</span>
            <input value={mobileNumber} onChange={(e) => setMobileNumber(e.target.value)} />
            {fieldErrors.mobile_number ? (
              <em className="field-error">{fieldErrors.mobile_number}</em>
            ) : null}
          </label>
          <label className="field">
            <span>Alternate mobile</span>
            <input
              value={alternateMobile}
              onChange={(e) => setAlternateMobile(e.target.value)}
            />
          </label>
        </div>

        <div className="form-row form-row--3">
          <label className="field">
            <span>Date of birth</span>
            <input
              type="date"
              value={dateOfBirth}
              onChange={(e) => setDateOfBirth(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Gender</span>
            <select value={gender} onChange={(e) => setGender(e.target.value)}>
              {GENDERS.map((item) => (
                <option key={item.value || 'blank'} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Blood group</span>
            <select value={bloodGroup} onChange={(e) => setBloodGroup(e.target.value)}>
              {BLOOD_GROUPS.map((item) => (
                <option key={item || 'blank'} value={item}>
                  {item || 'Select'}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="field">
          <span>Address</span>
          <input value={addressLine1} onChange={(e) => setAddressLine1(e.target.value)} />
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
            <span>Postal code</span>
            <input value={postalCode} onChange={(e) => setPostalCode(e.target.value)} />
          </label>
          <label className="field">
            <span>Mother language</span>
            <input value={motherLanguage} onChange={(e) => setMotherLanguage(e.target.value)} />
          </label>
        </div>

        <label className="field">
          <span>Languages known</span>
          <input
            value={languagesKnown}
            onChange={(e) => setLanguagesKnown(e.target.value)}
            placeholder="English, Tamil, Hindi"
          />
        </label>

        <div className="settings-form__actions">
          <Button type="submit" size="lg" loading={saving}>
            Save profile
          </Button>
        </div>
      </form>
    </div>
  );
}
