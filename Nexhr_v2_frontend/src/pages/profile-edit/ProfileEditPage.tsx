import { type ChangeEvent, type FormEvent, useEffect, useRef, useState } from 'react';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import { getInitial } from '../../utils/initials';
import type { EmployeeBankDetail, EmployeeEducationDetail, EmployeeJobExperience } from '../../types';
import './ProfileEditPage.css';

const GENDERS = [
  { value: '', label: 'Select gender' },
  { value: 'male', label: 'Male' },
  { value: 'female', label: 'Female' },
  { value: 'other', label: 'Other' },
  { value: 'prefer_not_to_say', label: 'Prefer not to say' },
];

const BLOOD_GROUPS = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'unknown'];

const EMPTY_BANK_ROW: EmployeeBankDetail = {
  account_holder_name: '',
  bank_name: '',
  account_number: '',
  ifsc_code: '',
  is_primary: false,
};

const EMPTY_EDUCATION_ROW: EmployeeEducationDetail = {
  degree: '',
  institution: '',
  field_of_study: '',
  year_of_passing: null,
  grade: '',
};

const EMPTY_EXPERIENCE_ROW: EmployeeJobExperience = {
  company_name: '',
  job_title: '',
  start_date: null,
  end_date: null,
  is_current: false,
  location: '',
  description: '',
};

export function ProfileEditPage() {
  const auth = useAuth();
  const workspace = useWorkspace();
  const profile = workspace.profile;
  const token = tokenStorage.getAccessToken();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [profilePhoto, setProfilePhoto] = useState('');
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [clearPhoto, setClearPhoto] = useState(false);
  const [mobileNumber, setMobileNumber] = useState('');
  const [alternateMobile, setAlternateMobile] = useState('');
  const [emergencyContactName, setEmergencyContactName] = useState('');
  const [emergencyContactRelationship, setEmergencyContactRelationship] = useState('');
  const [emergencyContactPhone, setEmergencyContactPhone] = useState('');
  const [bankDetails, setBankDetails] = useState<EmployeeBankDetail[]>([]);
  const [educationDetails, setEducationDetails] = useState<EmployeeEducationDetail[]>([]);
  const [jobExperiences, setJobExperiences] = useState<EmployeeJobExperience[]>([]);
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
    setPhotoFile(null);
    setPhotoPreview(null);
    setClearPhoto(false);
    setMobileNumber(profile.mobile_number);
    setAlternateMobile(profile.alternate_mobile);
    setEmergencyContactName(profile.emergency_contact_name || '');
    setEmergencyContactRelationship(profile.emergency_contact_relationship || '');
    setEmergencyContactPhone(profile.emergency_contact_phone || '');
    setBankDetails(profile.bank_details || []);
    setEducationDetails(profile.education_details || []);
    setJobExperiences(profile.job_experiences || []);
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

  useEffect(() => {
    return () => {
      if (photoPreview) URL.revokeObjectURL(photoPreview);
    };
  }, [photoPreview]);

  if (!profile) {
    return <div className="profile-edit">Profile not found.</div>;
  }

  const previewInitial = getInitial(displayName, firstName, profile.email, 'U');
  const shownPhoto = clearPhoto ? null : photoPreview || profilePhoto || null;

  function onPhotoSelected(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setFieldErrors((prev) => ({ ...prev, profile_photo: 'Choose an image file.' }));
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setFieldErrors((prev) => ({ ...prev, profile_photo: 'Photo must be 2 MB or smaller.' }));
      return;
    }
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoFile(file);
    setPhotoPreview(URL.createObjectURL(file));
    setClearPhoto(false);
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next.profile_photo;
      return next;
    });
  }

  function removePhoto() {
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoFile(null);
    setPhotoPreview(null);
    setClearPhoto(Boolean(profilePhoto));
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function updateBankRow(index: number, patch: Partial<EmployeeBankDetail>) {
    setBankDetails((prev) => prev.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }

  function addBankRow() {
    setBankDetails((prev) => [...prev, { ...EMPTY_BANK_ROW, is_primary: prev.length === 0 }]);
  }

  function removeBankRow(index: number) {
    setBankDetails((prev) => prev.filter((_, i) => i !== index));
  }

  function setPrimaryBank(index: number) {
    setBankDetails((prev) => prev.map((row, i) => ({ ...row, is_primary: i === index })));
  }

  function updateEducationRow(index: number, patch: Partial<EmployeeEducationDetail>) {
    setEducationDetails((prev) => prev.map((row, i) => (i === index ? { ...row, ...patch } : row)));
  }

  function addEducationRow() {
    setEducationDetails((prev) => [...prev, { ...EMPTY_EDUCATION_ROW }]);
  }

  function removeEducationRow(index: number) {
    setEducationDetails((prev) => prev.filter((_, i) => i !== index));
  }

  function updateExperienceRow(index: number, patch: Partial<EmployeeJobExperience>) {
    setJobExperiences((prev) =>
      prev.map((row, i) => {
        if (i !== index) return row;
        const next = { ...row, ...patch };
        if (patch.is_current === true) next.end_date = null;
        return next;
      }),
    );
  }

  function addExperienceRow() {
    setJobExperiences((prev) => [...prev, { ...EMPTY_EXPERIENCE_ROW }]);
  }

  function removeExperienceRow(index: number) {
    setJobExperiences((prev) => prev.filter((_, i) => i !== index));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSaving(true);
    setError(null);
    setMessage(null);
    setFieldErrors({});
    try {
      const form = new FormData();
      form.append('first_name', firstName.trim());
      form.append('last_name', lastName.trim());
      form.append('display_name', displayName.trim());
      form.append('mobile_number', mobileNumber.trim());
      form.append('alternate_mobile', alternateMobile.trim());
      form.append('emergency_contact_name', emergencyContactName.trim());
      form.append('emergency_contact_relationship', emergencyContactRelationship.trim());
      form.append('emergency_contact_phone', emergencyContactPhone.trim());
      form.append(
        'bank_details',
        JSON.stringify(
          bankDetails
            .map((row) => ({
              account_holder_name: row.account_holder_name.trim(),
              bank_name: row.bank_name.trim(),
              account_number: row.account_number.trim().replace(/[\s-]/g, ''),
              ifsc_code: row.ifsc_code.trim().toUpperCase().replace(/\s+/g, ''),
              is_primary: Boolean(row.is_primary),
            }))
            .filter(
              (row) =>
                row.account_holder_name ||
                row.bank_name ||
                row.account_number ||
                row.ifsc_code,
            ),
        ),
      );
      form.append(
        'education_details',
        JSON.stringify(
          educationDetails
            .map((row) => ({
              degree: row.degree.trim(),
              institution: row.institution.trim(),
              field_of_study: row.field_of_study.trim(),
              grade: row.grade.trim(),
              year_of_passing:
                row.year_of_passing === null ||
                row.year_of_passing === undefined ||
                Number.isNaN(Number(row.year_of_passing))
                  ? null
                  : Number(row.year_of_passing),
            }))
            .filter(
              (row) =>
                row.degree ||
                row.institution ||
                row.field_of_study ||
                row.grade ||
                row.year_of_passing != null,
            ),
        ),
      );
      form.append(
        'job_experiences',
        JSON.stringify(
          jobExperiences
            .map((row) => ({
              company_name: row.company_name.trim(),
              job_title: row.job_title.trim(),
              start_date: row.start_date || null,
              end_date: row.is_current ? null : row.end_date || null,
              is_current: Boolean(row.is_current),
              location: row.location.trim(),
              description: row.description.trim(),
            }))
            .filter(
              (row) =>
                row.company_name ||
                row.job_title ||
                row.start_date ||
                row.end_date ||
                row.location ||
                row.description ||
                row.is_current,
            ),
        ),
      );
      form.append('date_of_birth', dateOfBirth || '');
      form.append('gender', gender);
      form.append('blood_group', bloodGroup);
      form.append('country', country.trim());
      form.append('state', state.trim());
      form.append('city', city.trim());
      form.append('address_line1', addressLine1.trim());
      form.append('postal_code', postalCode.trim());
      form.append('mother_language', motherLanguage.trim());
      form.append('languages_known', languagesKnown.trim());
      if (photoFile) form.append('profile_photo', photoFile);
      if (clearPhoto) form.append('clear_profile_photo', 'true');

      const updated = await organizationApi.updateProfile(token, form);
      workspace.setProfile(updated);
      await auth.refreshUser();
      setPhotoFile(null);
      if (photoPreview) URL.revokeObjectURL(photoPreview);
      setPhotoPreview(null);
      setClearPhoto(false);
      setProfilePhoto(updated.profile_photo);
      setBankDetails(updated.bank_details || []);
      setEducationDetails(updated.education_details || []);
      setJobExperiences(updated.job_experiences || []);
      setMessage('Profile updated successfully.');
    } catch (err) {
      const nextFieldErrors = extractFieldErrors(err);
      setFieldErrors(nextFieldErrors);
      const firstFieldError = Object.values(nextFieldErrors)[0];
      setError(firstFieldError || extractErrorMessage(err, 'Unable to update profile.'));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="profile-edit">
      <p className="profile-edit__lead">
        Update how you appear across NexHr — photo, contact, and personal details.
      </p>

      <form className="profile-edit__form" onSubmit={onSubmit} noValidate>
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

        <section className="profile-edit__hero">
          <div className="profile-edit__avatar-wrap">
            {shownPhoto ? (
              <img src={shownPhoto} alt="" className="profile-edit__avatar" />
            ) : (
              <span className="profile-edit__avatar profile-edit__avatar--fallback" aria-hidden>
                {previewInitial}
              </span>
            )}
          </div>
          <div className="profile-edit__hero-copy">
            <p className="profile-edit__eyebrow">Your photo</p>
            <h2>{displayName || 'Your profile'}</h2>
            <p>Upload a clear square photo. JPG, PNG, WEBP or GIF up to 2 MB.</p>
            <div className="profile-edit__photo-actions">
              <Button type="button" variant="secondary" onClick={() => fileInputRef.current?.click()}>
                Upload photo
              </Button>
              {shownPhoto ? (
                <Button type="button" variant="ghost" onClick={removePhoto}>
                  Remove
                </Button>
              ) : null}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              className="profile-edit__file-input"
              onChange={onPhotoSelected}
            />
            {fieldErrors.profile_photo ? (
              <em className="field-error">{fieldErrors.profile_photo}</em>
            ) : null}
          </div>
        </section>

        <section className="profile-edit__card">
          <header className="profile-edit__card-head">
            <h3>Identity</h3>
            <p>Names and contact details used across the workspace.</p>
          </header>
          <div className="profile-edit__grid">
            <label className="field">
              <span>First name</span>
              <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
            </label>
            <label className="field">
              <span>Last name</span>
              <input value={lastName} onChange={(e) => setLastName(e.target.value)} />
            </label>
            <label className="field profile-edit__span-2">
              <span>Display name</span>
              <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
            </label>
            <label className="field profile-edit__span-2">
              <span>Email</span>
              <input value={profile.email} disabled />
            </label>
            <label className="field">
              <span>Mobile number</span>
              <input value={mobileNumber} onChange={(e) => setMobileNumber(e.target.value)} />
              {fieldErrors.mobile_number ? (
                <em className="field-error">{fieldErrors.mobile_number}</em>
              ) : null}
            </label>
            <label className="field">
              <span>Alternate mobile</span>
              <input value={alternateMobile} onChange={(e) => setAlternateMobile(e.target.value)} />
            </label>
          </div>
        </section>

        <section className="profile-edit__card">
          <header className="profile-edit__card-head">
            <h3>Emergency contact</h3>
            <p>Who to reach in case of an emergency.</p>
          </header>
          <div className="profile-edit__grid">
            <label className="field">
              <span>Contact name</span>
              <input
                value={emergencyContactName}
                onChange={(e) => setEmergencyContactName(e.target.value)}
              />
            </label>
            <label className="field">
              <span>Relationship</span>
              <input
                value={emergencyContactRelationship}
                onChange={(e) => setEmergencyContactRelationship(e.target.value)}
                placeholder="Spouse, Parent, Sibling…"
              />
            </label>
            <label className="field">
              <span>Phone</span>
              <input
                value={emergencyContactPhone}
                onChange={(e) => setEmergencyContactPhone(e.target.value)}
              />
              {fieldErrors.emergency_contact_phone ? (
                <em className="field-error">{fieldErrors.emergency_contact_phone}</em>
              ) : null}
            </label>
          </div>
        </section>

        <section className="profile-edit__card">
          <header className="profile-edit__card-head">
            <h3>Bank details</h3>
            <p>Salary accounts used for payroll transfers.</p>
          </header>
          {fieldErrors.bank_details ? (
            <em className="field-error">{fieldErrors.bank_details}</em>
          ) : null}
          <div className="profile-edit__repeat-list">
            {bankDetails.map((row, index) => (
              <div className="profile-edit__repeat-row" key={index}>
                <div className="profile-edit__grid">
                  <label className="field">
                    <span>Account holder name</span>
                    <input
                      value={row.account_holder_name}
                      onChange={(e) => updateBankRow(index, { account_holder_name: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Bank name</span>
                    <input
                      value={row.bank_name}
                      onChange={(e) => updateBankRow(index, { bank_name: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Account number</span>
                    <input
                      value={row.account_number}
                      onChange={(e) => updateBankRow(index, { account_number: e.target.value })}
                    />
                    {fieldErrors[`bank_details.${index}.account_number`] ? (
                      <em className="field-error">
                        {fieldErrors[`bank_details.${index}.account_number`]}
                      </em>
                    ) : null}
                  </label>
                  <label className="field">
                    <span>IFSC code</span>
                    <input
                      value={row.ifsc_code}
                      onChange={(e) => updateBankRow(index, { ifsc_code: e.target.value.toUpperCase() })}
                      placeholder="HDFC0001234"
                      maxLength={11}
                    />
                    {fieldErrors[`bank_details.${index}.ifsc_code`] ? (
                      <em className="field-error">
                        {fieldErrors[`bank_details.${index}.ifsc_code`]}
                      </em>
                    ) : null}
                  </label>
                  <label className="profile-edit__check">
                    <input
                      type="checkbox"
                      checked={row.is_primary}
                      onChange={() => setPrimaryBank(index)}
                    />
                    <span>Primary account</span>
                  </label>
                </div>
                <div className="profile-edit__repeat-actions">
                  <Button type="button" variant="ghost" onClick={() => removeBankRow(index)}>
                    Remove account
                  </Button>
                </div>
              </div>
            ))}
            {!bankDetails.length ? (
              <p className="profile-edit__empty">No bank accounts added yet.</p>
            ) : null}
          </div>
          <Button type="button" variant="secondary" onClick={addBankRow}>
            Add bank account
          </Button>
        </section>

        <section className="profile-edit__card">
          <header className="profile-edit__card-head">
            <h3>Education</h3>
            <p>Academic qualifications on file.</p>
          </header>
          {fieldErrors.education_details ? (
            <em className="field-error">{fieldErrors.education_details}</em>
          ) : null}
          <div className="profile-edit__repeat-list">
            {educationDetails.map((row, index) => (
              <div className="profile-edit__repeat-row" key={index}>
                <div className="profile-edit__grid">
                  <label className="field">
                    <span>Degree</span>
                    <input
                      value={row.degree}
                      onChange={(e) => updateEducationRow(index, { degree: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Institution</span>
                    <input
                      value={row.institution}
                      onChange={(e) => updateEducationRow(index, { institution: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Field of study</span>
                    <input
                      value={row.field_of_study}
                      onChange={(e) => updateEducationRow(index, { field_of_study: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Year of passing</span>
                    <input
                      type="number"
                      value={row.year_of_passing ?? ''}
                      onChange={(e) =>
                        updateEducationRow(index, {
                          year_of_passing: e.target.value === '' ? null : Number(e.target.value),
                        })
                      }
                      placeholder="2020"
                    />
                  </label>
                  <label className="field">
                    <span>Grade</span>
                    <input
                      value={row.grade}
                      onChange={(e) => updateEducationRow(index, { grade: e.target.value })}
                    />
                  </label>
                </div>
                <div className="profile-edit__repeat-actions">
                  <Button type="button" variant="ghost" onClick={() => removeEducationRow(index)}>
                    Remove entry
                  </Button>
                </div>
              </div>
            ))}
            {!educationDetails.length ? (
              <p className="profile-edit__empty">No education entries added yet.</p>
            ) : null}
          </div>
          <Button type="button" variant="secondary" onClick={addEducationRow}>
            Add education entry
          </Button>
        </section>

        <section className="profile-edit__card">
          <header className="profile-edit__card-head">
            <h3>Job experience</h3>
            <p>Prior roles and companies on your profile.</p>
          </header>
          {fieldErrors.job_experiences ? (
            <em className="field-error">{fieldErrors.job_experiences}</em>
          ) : null}
          <div className="profile-edit__repeat-list">
            {jobExperiences.map((row, index) => (
              <div className="profile-edit__repeat-row" key={index}>
                <div className="profile-edit__grid">
                  <label className="field">
                    <span>Company</span>
                    <input
                      value={row.company_name}
                      onChange={(e) => updateExperienceRow(index, { company_name: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Job title</span>
                    <input
                      value={row.job_title}
                      onChange={(e) => updateExperienceRow(index, { job_title: e.target.value })}
                    />
                  </label>
                  <label className="field">
                    <span>Start date</span>
                    <input
                      type="date"
                      value={row.start_date || ''}
                      onChange={(e) =>
                        updateExperienceRow(index, { start_date: e.target.value || null })
                      }
                    />
                  </label>
                  <label className="field">
                    <span>End date</span>
                    <input
                      type="date"
                      value={row.end_date || ''}
                      onChange={(e) =>
                        updateExperienceRow(index, { end_date: e.target.value || null })
                      }
                      disabled={row.is_current}
                    />
                    {fieldErrors[`job_experiences.${index}.end_date`] ? (
                      <em className="field-error">
                        {fieldErrors[`job_experiences.${index}.end_date`]}
                      </em>
                    ) : null}
                  </label>
                  <label className="field">
                    <span>Location</span>
                    <input
                      value={row.location}
                      onChange={(e) => updateExperienceRow(index, { location: e.target.value })}
                    />
                  </label>
                  <label className="profile-edit__check">
                    <input
                      type="checkbox"
                      checked={row.is_current}
                      onChange={(e) =>
                        updateExperienceRow(index, { is_current: e.target.checked })
                      }
                    />
                    <span>Currently working here</span>
                  </label>
                  <label className="field profile-edit__span-2">
                    <span>Description</span>
                    <textarea
                      rows={3}
                      value={row.description}
                      onChange={(e) => updateExperienceRow(index, { description: e.target.value })}
                    />
                  </label>
                </div>
                <div className="profile-edit__repeat-actions">
                  <Button type="button" variant="ghost" onClick={() => removeExperienceRow(index)}>
                    Remove entry
                  </Button>
                </div>
              </div>
            ))}
            {!jobExperiences.length ? (
              <p className="profile-edit__empty">No experience entries added yet.</p>
            ) : null}
          </div>
          <Button type="button" variant="secondary" onClick={addExperienceRow}>
            Add experience entry
          </Button>
        </section>

        <section className="profile-edit__card">
          <header className="profile-edit__card-head">
            <h3>Personal</h3>
            <p>Optional details that help HR keep records complete.</p>
          </header>
          <div className="profile-edit__grid profile-edit__grid--3">
            <label className="field">
              <span>Date of birth</span>
              <input type="date" value={dateOfBirth} onChange={(e) => setDateOfBirth(e.target.value)} />
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
            <label className="field">
              <span>Mother language</span>
              <input value={motherLanguage} onChange={(e) => setMotherLanguage(e.target.value)} />
            </label>
            <label className="field profile-edit__span-2">
              <span>Languages known</span>
              <input
                value={languagesKnown}
                onChange={(e) => setLanguagesKnown(e.target.value)}
                placeholder="English, Tamil, Hindi"
              />
            </label>
          </div>
        </section>

        <section className="profile-edit__card">
          <header className="profile-edit__card-head">
            <h3>Address</h3>
            <p>Where you can be reached for workplace correspondence.</p>
          </header>
          <div className="profile-edit__grid">
            <label className="field profile-edit__span-2">
              <span>Address line</span>
              <input value={addressLine1} onChange={(e) => setAddressLine1(e.target.value)} />
            </label>
            <label className="field">
              <span>City</span>
              <input value={city} onChange={(e) => setCity(e.target.value)} />
            </label>
            <label className="field">
              <span>State</span>
              <input value={state} onChange={(e) => setStateValue(e.target.value)} />
            </label>
            <label className="field">
              <span>Country</span>
              <input value={country} onChange={(e) => setCountry(e.target.value)} />
            </label>
            <label className="field">
              <span>Postal code</span>
              <input value={postalCode} onChange={(e) => setPostalCode(e.target.value)} />
            </label>
          </div>
        </section>

        <div className="profile-edit__actions">
          <Button type="submit" size="lg" loading={saving}>
            Save profile
          </Button>
        </div>
      </form>
    </div>
  );
}
