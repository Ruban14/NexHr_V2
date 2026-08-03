import {
  type ChangeEvent,
  type CSSProperties,
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { organizationApi } from '../../api/auth';
import { extractErrorMessage, extractFieldErrors } from '../../api/client';
import { tokenStorage } from '../../auth/tokenStorage';
import { Button } from '../../components/Button';
import { EmployeeDocumentsPanel } from '../../components/employees/EmployeeDocumentsPanel';
import { EmployeeAssetsPanel } from '../../components/employees/EmployeeAssetsPanel';
import { EmployeeAttendancePanel } from '../../components/employees/EmployeeAttendancePanel';
import { EmployeeLeavesPanel } from '../../components/employees/EmployeeLeavesPanel';
import { LoadingSkeleton } from '../../components/ui/LoadingSkeleton';
import { Modal } from '../../components/ui/Modal';
import { PageHeader } from '../../components/ui/PageHeader';
import type {
  EmployeeBankDetail,
  EmployeeEducationDetail,
  EmployeeJobExperience,
  EmployeeRecord,
  EmployeeTaxDetail,
  LifecycleHistoryEntry,
  LifecycleStatus,
  LifecycleTransition,
} from '../../types';
import { getInitial } from '../../utils/initials';
import { lifecycleStatusTone } from '../../utils/lifecycleStatus';
import { useWorkspace } from '../../workspace/WorkspaceContext';
import './EmployeesPage.css';

type DetailTab =
  | 'profile'
  | 'contact'
  | 'bank'
  | 'tax'
  | 'education'
  | 'experience'
  | 'role'
  | 'documents'
  | 'assets'
  | 'attendance'
  | 'timeline'
  | 'activities'
  | 'leaves';

type EmpNavIconName =
  | 'profile'
  | 'contact'
  | 'bank'
  | 'tax'
  | 'education'
  | 'experience'
  | 'role'
  | 'documents'
  | 'assets'
  | 'attendance'
  | 'timeline'
  | 'activities'
  | 'leaves';

const TABS: { id: DetailTab; label: string; description: string; icon: EmpNavIconName }[] = [
  { id: 'profile', label: 'Profile', description: 'Identity & personal', icon: 'profile' },
  { id: 'contact', label: 'Contact', description: 'Phone & address', icon: 'contact' },
  { id: 'bank', label: 'Bank', description: 'Salary accounts', icon: 'bank' },
  { id: 'tax', label: 'Tax', description: 'PAN, PF & ESI', icon: 'tax' },
  { id: 'education', label: 'Education', description: 'Degrees & schools', icon: 'education' },
  { id: 'experience', label: 'Experience', description: 'Work history', icon: 'experience' },
  { id: 'role', label: 'Role', description: 'Designation & access', icon: 'role' },
  { id: 'documents', label: 'Documents', description: 'Uploads & checklist', icon: 'documents' },
  { id: 'assets', label: 'Assets', description: 'Assign & revoke', icon: 'assets' },
  { id: 'attendance', label: 'Attendance', description: 'Punches & hours', icon: 'attendance' },
  { id: 'timeline', label: 'Timeline', description: 'Lifecycle journey', icon: 'timeline' },
  { id: 'activities', label: 'Activities', description: 'Audit history', icon: 'activities' },
  { id: 'leaves', label: 'Leaves', description: 'Balances & requests', icon: 'leaves' },
];

const NAV_GROUPS: { label: string; ids: DetailTab[] }[] = [
  {
    label: 'Details',
    ids: ['profile', 'contact', 'bank', 'tax', 'education', 'experience', 'role'],
  },
  {
    label: 'Workplace',
    ids: ['documents', 'assets', 'attendance', 'timeline', 'activities', 'leaves'],
  },
];

const TAB_BY_ID = Object.fromEntries(TABS.map((tab) => [tab.id, tab])) as Record<
  DetailTab,
  (typeof TABS)[number]
>;

function EmpProfileNavIcon({ name }: { name: EmpNavIconName }) {
  const common = {
    viewBox: '0 0 24 24',
    width: 18,
    height: 18,
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.8,
    'aria-hidden': true as const,
  };

  switch (name) {
    case 'profile':
      return (
        <svg {...common}>
          <circle cx="12" cy="8" r="3.2" />
          <path d="M5 19.5a7 7 0 0 1 14 0" />
        </svg>
      );
    case 'contact':
      return (
        <svg {...common}>
          <path d="M7 4.5h10a1.5 1.5 0 0 1 1.5 1.5v12a1.5 1.5 0 0 1-1.5 1.5H7A1.5 1.5 0 0 1 5.5 18V6A1.5 1.5 0 0 1 7 4.5z" />
          <path d="M9 9h6M9 12.5h6M9 16h3.5" />
        </svg>
      );
    case 'bank':
      return (
        <svg {...common}>
          <path d="M4 10h16M5.5 10V18M18.5 10V18M4 18h16M12 5l8 5H4l8-5z" />
        </svg>
      );
    case 'tax':
      return (
        <svg {...common}>
          <rect x="4.5" y="5" width="15" height="14" rx="2" />
          <path d="M8 9.5h8M8 13h5" />
        </svg>
      );
    case 'education':
      return (
        <svg {...common}>
          <path d="M3.5 10 12 5.5 20.5 10 12 14.5 3.5 10z" />
          <path d="M7 12.2v4.3c0 .9 2.2 2.5 5 2.5s5-1.6 5-2.5v-4.3" />
        </svg>
      );
    case 'experience':
      return (
        <svg {...common}>
          <rect x="4" y="8" width="16" height="11" rx="2" />
          <path d="M9 8V6.5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2V8" />
        </svg>
      );
    case 'role':
      return (
        <svg {...common}>
          <circle cx="12" cy="5" r="2.2" />
          <circle cx="6" cy="18" r="2.2" />
          <circle cx="18" cy="18" r="2.2" />
          <path d="M12 7.2v4.3M12 11.5 6.8 16M12 11.5l5.2 4.5" />
        </svg>
      );
    case 'documents':
      return (
        <svg {...common}>
          <path d="M7 3.5h7.5L19 8v12.5a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4.5a1 1 0 0 1 1-1z" />
          <path d="M14 3.5V8h5M9 12h6M9 15.5h6" />
        </svg>
      );
    case 'assets':
      return (
        <svg {...common}>
          <rect x="3.5" y="7" width="17" height="12" rx="2" />
          <path d="M8 7V5.5A1.5 1.5 0 0 1 9.5 4h5A1.5 1.5 0 0 1 16 5.5V7M8 12h8M8 15.5h5" />
        </svg>
      );
    case 'attendance':
      return (
        <svg {...common}>
          <circle cx="12" cy="12" r="8" />
          <path d="M12 8v4l2.5 1.5" />
        </svg>
      );
    case 'timeline':
      return (
        <svg {...common}>
          <path d="M12 4v16" />
          <circle cx="12" cy="6" r="2" />
          <circle cx="12" cy="12" r="2" />
          <circle cx="12" cy="18" r="2" />
        </svg>
      );
    case 'activities':
      return (
        <svg {...common}>
          <path d="M5 6.5h14M5 12h14M5 17.5h9" />
        </svg>
      );
    case 'leaves':
      return (
        <svg {...common}>
          <path d="M8 4h8a2 2 0 0 1 2 2v14l-6-3-6 3V6a2 2 0 0 1 2-2z" />
        </svg>
      );
  }
}

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

const EMPTY_TAX_DETAIL: EmployeeTaxDetail = {
  pan_number: '',
  aadhaar_number: '',
  uan_number: '',
  pf_number: '',
  esi_number: '',
  tax_regime: 'new',
  tax_identification_number: '',
  is_pf_applicable: true,
  is_esi_applicable: false,
  professional_tax_applicable: false,
  labour_welfare_fund_applicable: false,
};

type EditFormState = {
  display_name: string;
  first_name: string;
  last_name: string;
  email: string;
  employee_code: string;
  mobile_number: string;
  alternate_mobile: string;
  emergency_contact_name: string;
  emergency_contact_relationship: string;
  emergency_contact_phone: string;
  bank_details: EmployeeBankDetail[];
  education_details: EmployeeEducationDetail[];
  job_experiences: EmployeeJobExperience[];
  tax_detail: EmployeeTaxDetail;
  date_of_birth: string;
  gender: string;
  blood_group: string;
  country: string;
  state: string;
  city: string;
  address_line1: string;
  postal_code: string;
  mother_language: string;
  languages_known: string;
  designation_id: string;
  reporting_manager_id: string;
  employee_type_id: string;
  access_type_id: string;
  joining_date: string;
  exit_date: string;
  is_active: boolean;
};

function formatTimelineDate(iso: string | null): string {
  if (!iso) return 'Pending';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return 'Pending';
  return date.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function formatTimelineTime(iso: string | null): string | null {
  if (!iso) return null;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return null;
  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function latestChangeForStatus(
  statusId: string,
  history: LifecycleHistoryEntry[] | undefined,
): string | null {
  if (!history?.length) return null;
  const matches = history.filter((row) => row.to_status.id === statusId);
  if (!matches.length) return null;
  return matches.reduce((latest, row) =>
    new Date(row.changed_at) > new Date(latest.changed_at) ? row : latest,
  ).changed_at;
}

function sortEducationByYear(rows: EmployeeEducationDetail[]): EmployeeEducationDetail[] {
  return [...rows].sort((a, b) => {
    const yearA = a.year_of_passing;
    const yearB = b.year_of_passing;
    if (yearA == null && yearB == null) return 0;
    if (yearA == null) return 1;
    if (yearB == null) return -1;
    if (yearA !== yearB) return yearA - yearB;
    return (a.degree || '').localeCompare(b.degree || '');
  });
}

function sortExperiences(rows: EmployeeJobExperience[]): EmployeeJobExperience[] {
  return [...rows].sort((a, b) => {
    if (a.is_current !== b.is_current) return a.is_current ? -1 : 1;
    const aStart = a.start_date || '';
    const bStart = b.start_date || '';
    return bStart.localeCompare(aStart);
  });
}

function formatExperienceMonth(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString(undefined, { month: 'short', year: 'numeric' });
}

function experienceDateParts(row: EmployeeJobExperience): { start: string; end: string } {
  return {
    start: formatExperienceMonth(row.start_date) || 'Start TBD',
    end: row.is_current ? 'Present' : formatExperienceMonth(row.end_date) || 'End TBD',
  };
}

function experienceEndDate(row: EmployeeJobExperience): Date | null {
  if (row.is_current) return new Date();
  if (!row.end_date) return null;
  const date = new Date(`${row.end_date}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function experienceStartDate(row: EmployeeJobExperience): Date | null {
  if (!row.start_date) return null;
  const date = new Date(`${row.start_date}T00:00:00`);
  return Number.isNaN(date.getTime()) ? null : date;
}

function tenureMonths(row: EmployeeJobExperience): number {
  const start = experienceStartDate(row);
  const end = experienceEndDate(row);
  if (!start || !end || end < start) return 0;
  const months =
    (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth()) + 1;
  return Math.max(0, months);
}

function formatTenure(months: number): string {
  if (months <= 0) return '—';
  const years = Math.floor(months / 12);
  const rem = months % 12;
  if (years && rem) return `${years}y ${rem}m`;
  if (years) return `${years}y`;
  return `${rem}m`;
}

function buildExperienceInsights(rows: EmployeeJobExperience[]) {
  const tenures = rows.map((row) => ({ row, months: tenureMonths(row) }));
  const totalMonths = tenures.reduce((sum, item) => sum + item.months, 0);
  const companies = new Set(
    rows.map((row) => row.company_name.trim().toLowerCase()).filter(Boolean),
  );
  const longest = tenures.reduce(
    (best, item) => (item.months > best.months ? item : best),
    { row: null as EmployeeJobExperience | null, months: 0 },
  );
  const maxMonths = Math.max(1, ...tenures.map((item) => item.months), 1);
  const current = rows.find((row) => row.is_current) || null;
  return {
    roleCount: rows.length,
    companyCount: companies.size,
    totalMonths,
    totalLabel: formatTenure(totalMonths),
    longestLabel: longest.row
      ? longest.row.job_title || longest.row.company_name || formatTenure(longest.months)
      : '—',
    longestMonths: longest.months,
    currentTitle: current?.job_title || null,
    maxMonths,
    tenures,
  };
}

function Fact({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="emp-profile__fact">
      <span>{label}</span>
      <strong>{value || '—'}</strong>
    </div>
  );
}

function FormSaveBar({ saving, onCancel }: { saving: boolean; onCancel: () => void }) {
  return (
    <div className="emp-profile__form-footer">
      <Button type="button" variant="ghost" onClick={onCancel} disabled={saving}>
        Cancel
      </Button>
      <Button type="submit" loading={saving}>
        Save changes
      </Button>
    </div>
  );
}

function toEditForm(employee: EmployeeRecord): EditFormState {
  return {
    display_name: employee.display_name || '',
    first_name: employee.first_name || '',
    last_name: employee.last_name || '',
    email: employee.email || '',
    employee_code: employee.employee_code || '',
    mobile_number: employee.mobile_number || '',
    alternate_mobile: employee.alternate_mobile || '',
    emergency_contact_name: employee.emergency_contact_name || '',
    emergency_contact_relationship: employee.emergency_contact_relationship || '',
    emergency_contact_phone: employee.emergency_contact_phone || '',
    bank_details: employee.bank_details || [],
    education_details: employee.education_details || [],
    job_experiences: employee.job_experiences || [],
    tax_detail: {
      ...EMPTY_TAX_DETAIL,
      ...(employee.tax_detail || {}),
      tax_regime: employee.tax_detail?.tax_regime || 'new',
    },
    date_of_birth: employee.date_of_birth || '',
    gender: employee.gender || '',
    blood_group: employee.blood_group || '',
    country: employee.country || '',
    state: employee.state || '',
    city: employee.city || '',
    address_line1: employee.address_line1 || '',
    postal_code: employee.postal_code || '',
    mother_language: employee.mother_language || '',
    languages_known: (employee.languages_known || []).join(', '),
    designation_id: employee.designation_id || '',
    reporting_manager_id: employee.reporting_manager_id || '',
    employee_type_id: employee.employee_type_id || '',
    access_type_id: employee.access_type_id || '',
    joining_date: employee.joining_date || '',
    exit_date: employee.exit_date || '',
    is_active: employee.is_active,
  };
}

function genderLabel(value?: string) {
  return GENDERS.find((item) => item.value === value)?.label || value || '—';
}

function bankInitials(name?: string) {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return 'BA';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0] || ''}${parts[1][0] || ''}`.toUpperCase();
}

function maskAccountNumber(value?: string) {
  const digits = (value || '').replace(/\s+/g, '');
  if (!digits) return '—';
  if (digits.length <= 4) return digits;
  return `•••• ${digits.slice(-4)}`;
}

function formatAccountNumber(value?: string) {
  const digits = (value || '').replace(/\s+/g, '');
  if (!digits) return '—';
  return digits.replace(/(\d{4})(?=\d)/g, '$1 ').trim();
}

export function EmployeeDetailPage() {
  const { employeeId = '' } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { currentBranch, organization, profile } = useWorkspace();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [employee, setEmployee] = useState<EmployeeRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [pendingTransition, setPendingTransition] = useState<LifecycleTransition | null>(null);
  const [transitionRemarks, setTransitionRemarks] = useState('');
  const [transitionExitDate, setTransitionExitDate] = useState('');
  const [activeTab, setActiveTab] = useState<DetailTab>('profile');
  const [editing, setEditing] = useState(false);
  const [taxRevealed, setTaxRevealed] = useState(false);
  const [bankRevealed, setBankRevealed] = useState(false);
  const [editForm, setEditForm] = useState<EditFormState | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [clearPhoto, setClearPhoto] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [managerOptions, setManagerOptions] = useState<EmployeeRecord[]>([]);

  const load = useCallback(async () => {
    const token = tokenStorage.getAccessToken();
    if (!token || !employeeId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await organizationApi.getEmployee(token, employeeId);
      setEmployee(data);
      setEditForm(toEditForm(data));
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to load employee.'));
      setEmployee(null);
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    void load();
  }, [load, currentBranch?.branch_id]);

  useEffect(() => {
    if (activeTab !== 'role' || !employeeId) return;
    const token = tokenStorage.getAccessToken();
    if (!token) return;
    void organizationApi
      .listEmployees(token, { page_size: 100 })
      .then((data) => {
        setManagerOptions(data.items.filter((row) => row.id !== employeeId && row.is_active));
      })
      .catch(() => {
        setManagerOptions([]);
      });
  }, [activeTab, employeeId, currentBranch?.branch_id]);

  useEffect(() => {
    setEditing(false);
    setTaxRevealed(false);
    setSaveMessage(null);
    setFieldErrors({});
    setPhotoFile(null);
    setClearPhoto(false);
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoPreview(null);
  }, [activeTab, employeeId]);

  useEffect(() => {
    return () => {
      if (photoPreview) URL.revokeObjectURL(photoPreview);
    };
  }, [photoPreview]);

  function todayDateInput(): string {
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function defaultNoticeExitDate(): string {
    const days = organization?.notice_period_days || 0;
    if (days < 1) return '';
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() + days);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  function defaultReleaseExitDate(): string {
    return employee?.exit_date || todayDateInput();
  }

  function transitionNeedsExitDate(key?: string) {
    return key === 'notice_period' || key === 'released';
  }

  async function runTransition(toStatusId: string, remarks?: string, exitDate?: string) {
    const token = tokenStorage.getAccessToken();
    if (!token || !employeeId) return;
    setActionLoading(toStatusId);
    setError(null);
    try {
      const data = await organizationApi.transitionEmployee(token, employeeId, {
        to_status_id: toStatusId,
        remarks: remarks?.trim() || undefined,
        exit_date: exitDate || undefined,
      });
      setEmployee(data);
      setEditForm(toEditForm(data));
      setPendingTransition(null);
      setTransitionRemarks('');
      setTransitionExitDate('');
    } catch (err) {
      setError(extractErrorMessage(err, 'Unable to update lifecycle status.'));
    } finally {
      setActionLoading(null);
    }
  }

  function openTransitionConfirm(transition: LifecycleTransition) {
    setTransitionRemarks('');
    if (transition.to_status.key === 'notice_period') {
      setTransitionExitDate(defaultNoticeExitDate());
    } else if (transition.to_status.key === 'released') {
      setTransitionExitDate(defaultReleaseExitDate());
    } else {
      setTransitionExitDate('');
    }
    setPendingTransition(transition);
    setError(null);
  }

  function closeTransitionConfirm() {
    if (actionLoading) return;
    setPendingTransition(null);
    setTransitionRemarks('');
    setTransitionExitDate('');
  }

  function startEditing() {
    if (!employee) return;
    setEditForm(toEditForm(employee));
    setFieldErrors({});
    setSaveMessage(null);
    setError(null);
    setPhotoFile(null);
    setClearPhoto(false);
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoPreview(null);
    setEditing(true);
  }

  function cancelEditing() {
    if (employee) setEditForm(toEditForm(employee));
    setFieldErrors({});
    setPhotoFile(null);
    setClearPhoto(false);
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoPreview(null);
    setEditing(false);
  }

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
    setClearPhoto(Boolean(employee?.profile_photo));
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function updateBankRow(index: number, patch: Partial<EmployeeBankDetail>) {
    setEditForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        bank_details: prev.bank_details.map((row, i) => (i === index ? { ...row, ...patch } : row)),
      };
    });
  }

  function addBankRow() {
    setEditForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        bank_details: [
          ...prev.bank_details,
          { ...EMPTY_BANK_ROW, is_primary: prev.bank_details.length === 0 },
        ],
      };
    });
  }

  function removeBankRow(index: number) {
    setEditForm((prev) => {
      if (!prev) return prev;
      return { ...prev, bank_details: prev.bank_details.filter((_, i) => i !== index) };
    });
  }

  function setPrimaryBank(index: number) {
    setEditForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        bank_details: prev.bank_details.map((row, i) => ({ ...row, is_primary: i === index })),
      };
    });
  }

  function updateEducationRow(index: number, patch: Partial<EmployeeEducationDetail>) {
    setEditForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        education_details: prev.education_details.map((row, i) =>
          i === index ? { ...row, ...patch } : row,
        ),
      };
    });
  }

  function addEducationRow() {
    setEditForm((prev) => {
      if (!prev) return prev;
      return { ...prev, education_details: [...prev.education_details, { ...EMPTY_EDUCATION_ROW }] };
    });
  }

  function removeEducationRow(index: number) {
    setEditForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        education_details: prev.education_details.filter((_, i) => i !== index),
      };
    });
  }

  function updateExperienceRow(index: number, patch: Partial<EmployeeJobExperience>) {
    setEditForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        job_experiences: prev.job_experiences.map((row, i) => {
          if (i !== index) return row;
          const next = { ...row, ...patch };
          if (patch.is_current === true) next.end_date = null;
          return next;
        }),
      };
    });
  }

  function addExperienceRow() {
    setEditForm((prev) => {
      if (!prev) return prev;
      return { ...prev, job_experiences: [...prev.job_experiences, { ...EMPTY_EXPERIENCE_ROW }] };
    });
  }

  function removeExperienceRow(index: number) {
    setEditForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        job_experiences: prev.job_experiences.filter((_, i) => i !== index),
      };
    });
  }

  function updateTaxDetail(patch: Partial<EmployeeTaxDetail>) {
    setEditForm((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        tax_detail: { ...prev.tax_detail, ...patch },
      };
    });
  }

  async function saveEmployee(event: FormEvent) {
    event.preventDefault();
    const token = tokenStorage.getAccessToken();
    if (!token || !employeeId || !editForm) return;
    setSaving(true);
    setError(null);
    setSaveMessage(null);
    setFieldErrors({});
    try {
      const form = new FormData();
      form.append('display_name', editForm.display_name.trim());
      form.append('first_name', editForm.first_name.trim());
      form.append('last_name', editForm.last_name.trim());
      if (employee?.email_editable !== false) {
        form.append('email', editForm.email.trim());
      }
      form.append('mobile_number', editForm.mobile_number.trim());
      form.append('alternate_mobile', editForm.alternate_mobile.trim());
      form.append('emergency_contact_name', editForm.emergency_contact_name.trim());
      form.append('emergency_contact_relationship', editForm.emergency_contact_relationship.trim());
      form.append('emergency_contact_phone', editForm.emergency_contact_phone.trim());
      form.append(
        'bank_details',
        JSON.stringify(
          editForm.bank_details
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
          editForm.education_details
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
          editForm.job_experiences
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
      form.append(
        'tax_detail',
        JSON.stringify({
          pan_number: editForm.tax_detail.pan_number.trim().toUpperCase().replace(/\s+/g, ''),
          aadhaar_number: editForm.tax_detail.aadhaar_number.replace(/\D/g, ''),
          uan_number: editForm.tax_detail.uan_number.trim(),
          pf_number: editForm.tax_detail.pf_number.trim(),
          esi_number: editForm.tax_detail.esi_number.trim(),
          tax_regime: editForm.tax_detail.tax_regime || 'new',
          tax_identification_number: editForm.tax_detail.tax_identification_number.trim(),
          is_pf_applicable: Boolean(editForm.tax_detail.is_pf_applicable),
          is_esi_applicable: Boolean(editForm.tax_detail.is_esi_applicable),
          professional_tax_applicable: Boolean(editForm.tax_detail.professional_tax_applicable),
          labour_welfare_fund_applicable: Boolean(
            editForm.tax_detail.labour_welfare_fund_applicable,
          ),
        }),
      );
      form.append('date_of_birth', editForm.date_of_birth || '');
      form.append('gender', editForm.gender);
      form.append('blood_group', editForm.blood_group);
      form.append('country', editForm.country.trim());
      form.append('state', editForm.state.trim());
      form.append('city', editForm.city.trim());
      form.append('address_line1', editForm.address_line1.trim());
      form.append('postal_code', editForm.postal_code.trim());
      form.append('mother_language', editForm.mother_language.trim());
      form.append('languages_known', editForm.languages_known.trim());
      form.append('designation_id', editForm.designation_id || '');
      form.append('reporting_manager_id', editForm.reporting_manager_id || '');
      form.append('employee_type_id', editForm.employee_type_id || '');
      form.append('access_type_id', editForm.access_type_id || '');
      form.append('joining_date', editForm.joining_date || '');
      form.append('exit_date', editForm.exit_date || '');
      form.append('is_active', editForm.is_active ? 'true' : 'false');
      if (photoFile) form.append('profile_photo', photoFile);
      if (clearPhoto) form.append('clear_profile_photo', 'true');

      const data = await organizationApi.updateEmployee(token, employeeId, form);
      setEmployee(data);
      setEditForm(toEditForm(data));
      setEditing(false);
      setPhotoFile(null);
      setClearPhoto(false);
      if (photoPreview) URL.revokeObjectURL(photoPreview);
      setPhotoPreview(null);
      setSaveMessage('Employee details updated.');
    } catch (err) {
      const nextFieldErrors = extractFieldErrors(err);
      setFieldErrors(nextFieldErrors);
      const firstFieldError = Object.values(nextFieldErrors)[0];
      setError(
        firstFieldError || extractErrorMessage(err, 'Unable to update employee.'),
      );
    } finally {
      setSaving(false);
    }
  }

  const timelineItems = useMemo(() => {
    if (!employee) {
      return [] as Array<{
        status: LifecycleStatus;
        isCurrent: boolean;
        isPast: boolean;
        changedAt: string | null;
      }>;
    }

    const currentId = employee.lifecycle_status.id;
    const visited = new Set(
      (employee.history || []).flatMap((row) =>
        [row.from_status?.id, row.to_status.id].filter(Boolean) as string[],
      ),
    );
    visited.add(currentId);

    return (employee.timeline_statuses || []).map((status) => {
      const isCurrent = status.id === currentId;
      const isPast = !isCurrent && visited.has(status.id);
      return {
        status,
        isCurrent,
        isPast,
        changedAt: latestChangeForStatus(status.id, employee.history),
      };
    });
  }, [employee]);

  const educationTree = useMemo(
    () => sortEducationByYear(employee?.education_details || []),
    [employee?.education_details],
  );

  const experienceList = useMemo(
    () => sortExperiences(employee?.job_experiences || []),
    [employee?.job_experiences],
  );

  const experienceInsights = useMemo(
    () => buildExperienceInsights(experienceList),
    [experienceList],
  );

  const isOwnProfile = Boolean(profile?.id && employee?.id === profile.id);

  const visibleNavGroups = useMemo(
    () =>
      NAV_GROUPS.map((group) => ({
        ...group,
        ids: group.ids.filter((id) => id !== 'attendance' || isOwnProfile),
      })).filter((group) => group.ids.length > 0),
    [isOwnProfile],
  );

  useEffect(() => {
    if (!isOwnProfile && activeTab === 'attendance') {
      setActiveTab('profile');
    }
  }, [isOwnProfile, activeTab]);

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (!tab) return;
    const allowed = TABS.some((item) => item.id === tab);
    if (!allowed) return;
    if (tab === 'attendance' && !isOwnProfile) return;
    setActiveTab(tab as DetailTab);
    const next = new URLSearchParams(searchParams);
    next.delete('tab');
    setSearchParams(next, { replace: true });
  }, [searchParams, setSearchParams, isOwnProfile]);

  if (loading) {
    return (
      <section className="employees">
        <LoadingSkeleton />
      </section>
    );
  }

  if (!employee || !editForm) {
    return (
      <section className="employees">
        <PageHeader title="Employee" description={error || 'Employee not found.'} />
        <Link to="/app/employees">Back to employees</Link>
      </section>
    );
  }

  const initial = getInitial(employee.display_name, employee.first_name, employee.email, 'E');
  const fullName =
    [employee.first_name, employee.last_name].filter(Boolean).join(' ').trim() ||
    employee.display_name;
  const shownPhoto = clearPhoto ? null : photoPreview || employee.profile_photo || null;
  const options = employee.master_options;
  const timelineCompleted = timelineItems.filter((item) => item.isPast || item.isCurrent).length;
  const timelineTotal = timelineItems.length;

  return (
    <section className="employees employees--detail">
      <header className="emp-profile__banner">
        <div className="emp-profile__identity">
          {shownPhoto && !editing ? (
            <img src={shownPhoto} alt="" className="emp-profile__avatar emp-profile__avatar--photo" />
          ) : (
            <div className="emp-profile__avatar" aria-hidden>
              {initial}
            </div>
          )}
          <div className="emp-profile__who">
            <p className="emp-profile__eyebrow">Employee profile</p>
            <h1>{employee.display_name}</h1>
            <p className="emp-profile__lead">
              {fullName !== employee.display_name ? `${fullName} · ` : null}
              {employee.email || 'No email on file'}
              {employee.employee_code ? ` · ${employee.employee_code}` : ''}
            </p>
            <div className="emp-profile__chips">
              <span
                className="employees__status-pill"
                data-lifecycle={lifecycleStatusTone(employee.lifecycle_status)}
              >
                {employee.lifecycle_status.name}
              </span>
              <span className="employees__chip">
                {employee.is_active ? 'Active record' : 'Inactive'}
              </span>
              {employee.employee_type_name ? (
                <span className="employees__chip">{employee.employee_type_name}</span>
              ) : null}
              {employee.designation_name ? (
                <span className="employees__chip">{employee.designation_name}</span>
              ) : null}
              {employee.joining_date ? (
                <span className="employees__chip">Joined {employee.joining_date}</span>
              ) : null}
            </div>
          </div>
        </div>
        <div className="emp-profile__banner-actions">
          <Link to="/app/employees" className="employees__back">
            Back to list
          </Link>
        </div>
      </header>

      {error ? <div className="auth-alert auth-alert--error">{error}</div> : null}
      {saveMessage ? <div className="auth-alert auth-alert--success">{saveMessage}</div> : null}

      <div className="emp-profile__body">
        <aside className="emp-profile__side" aria-label="Employee sections">
          <nav className="emp-profile__side-nav">
            {visibleNavGroups.map((group) => (
              <div key={group.label} className="emp-profile__side-group">
                <p className="emp-profile__side-label">{group.label}</p>
                {group.ids.map((id, index) => {
                  const tab = TAB_BY_ID[id];
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      className={`emp-profile__side-link ${activeTab === tab.id ? 'is-active' : ''}`}
                      aria-current={activeTab === tab.id ? 'page' : undefined}
                      style={{ '--nav-index': index } as CSSProperties}
                      onClick={() => {
                        setActiveTab(tab.id);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                    >
                      <span className="emp-profile__side-icon">
                        <EmpProfileNavIcon name={tab.icon} />
                      </span>
                      <span className="emp-profile__side-copy">
                        <strong>{tab.label}</strong>
                        <em>{tab.description}</em>
                      </span>
                    </button>
                  );
                })}
              </div>
            ))}
          </nav>
        </aside>

        <div className="employees__main" key={activeTab}>
          {activeTab === 'profile' ? (
            <>
              {editing ? (
                <form className="emp-profile__card emp-profile__card--edit" onSubmit={saveEmployee}>
                  <header className="emp-profile__card-head">
                    <div>
                      <h2>Edit profile</h2>
                      <p>Update photo, identity, and personal information.</p>
                    </div>
                  </header>

                  <div className="emp-profile__photo-edit">
                    {shownPhoto ? (
                      <img src={shownPhoto} alt="" className="emp-profile__photo-preview" />
                    ) : (
                      <span className="emp-profile__photo-preview emp-profile__photo-preview--fallback">
                        {initial}
                      </span>
                    )}
                    <div>
                      <strong>Profile photo</strong>
                      <p>JPG, PNG, WEBP or GIF up to 2 MB.</p>
                      <div className="emp-profile__edit-actions">
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
                        className="emp-profile__file-input"
                        onChange={onPhotoSelected}
                      />
                      {fieldErrors.profile_photo ? (
                        <em className="field-error">{fieldErrors.profile_photo}</em>
                      ) : null}
                    </div>
                  </div>

                  <h3 className="emp-profile__section-title">Identity</h3>
                  <div className="emp-profile__edit-grid">
                    <label className="field">
                      <span>Display name</span>
                      <input
                        value={editForm.display_name}
                        onChange={(e) => setEditForm({ ...editForm, display_name: e.target.value })}
                      />
                    </label>
                    <label className="field">
                      <span>Employee code</span>
                      <input value={editForm.employee_code} disabled readOnly />
                      <em className="emp-profile__field-hint">Assigned automatically.</em>
                    </label>
                    <label className="field">
                      <span>First name</span>
                      <input
                        value={editForm.first_name}
                        onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                      />
                    </label>
                    <label className="field">
                      <span>Last name</span>
                      <input
                        value={editForm.last_name}
                        onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                      />
                    </label>
                    <label className="field emp-profile__span-2">
                      <span>Email</span>
                      <input
                        type="email"
                        value={editForm.email}
                        disabled={employee.email_editable === false}
                        onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                      />
                      {employee.email_editable === false ? (
                        <em className="emp-profile__field-hint">
                          Verified email cannot be changed.
                        </em>
                      ) : null}
                      {fieldErrors.email ? <em className="field-error">{fieldErrors.email}</em> : null}
                    </label>
                  </div>

                  <h3 className="emp-profile__section-title">Personal</h3>
                  <div className="emp-profile__edit-grid">
                    <label className="field">
                      <span>Date of birth</span>
                      <input
                        type="date"
                        value={editForm.date_of_birth}
                        onChange={(e) => setEditForm({ ...editForm, date_of_birth: e.target.value })}
                      />
                    </label>
                    <label className="field">
                      <span>Gender</span>
                      <select
                        value={editForm.gender}
                        onChange={(e) => setEditForm({ ...editForm, gender: e.target.value })}
                      >
                        {GENDERS.map((item) => (
                          <option key={item.value || 'blank'} value={item.value}>
                            {item.label}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>Blood group</span>
                      <select
                        value={editForm.blood_group}
                        onChange={(e) => setEditForm({ ...editForm, blood_group: e.target.value })}
                      >
                        {BLOOD_GROUPS.map((item) => (
                          <option key={item || 'blank'} value={item}>
                            {item || 'Select'}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>Mother language</span>
                      <input
                        value={editForm.mother_language}
                        onChange={(e) => setEditForm({ ...editForm, mother_language: e.target.value })}
                      />
                    </label>
                    <label className="field emp-profile__span-2">
                      <span>Languages known</span>
                      <input
                        value={editForm.languages_known}
                        onChange={(e) => setEditForm({ ...editForm, languages_known: e.target.value })}
                        placeholder="English, Tamil, Hindi"
                      />
                    </label>
                  </div>

                  <FormSaveBar saving={saving} onCancel={cancelEditing} />
                </form>
              ) : (
                <>
                  <article className="emp-profile__card">
                    <header className="emp-profile__card-head emp-profile__card-head--row">
                      <div>
                        <h2>Identity</h2>
                        <p>Photo, names, and account identifiers for this employee.</p>
                      </div>
                      <Button type="button" variant="secondary" onClick={startEditing}>
                        Edit
                      </Button>
                    </header>
                    <div className="emp-profile__grid">
                      <Fact label="Display name" value={employee.display_name} />
                      <Fact label="Employee code" value={employee.employee_code} />
                      <Fact label="First name" value={employee.first_name} />
                      <Fact label="Last name" value={employee.last_name} />
                      <Fact label="Email" value={employee.email} />
                    </div>
                  </article>

                  <article className="emp-profile__card">
                    <header className="emp-profile__card-head emp-profile__card-head--row">
                      <div>
                        <h2>Personal details</h2>
                        <p>Personal information for this employee.</p>
                      </div>
                      <Button type="button" variant="secondary" onClick={startEditing}>
                        Edit
                      </Button>
                    </header>
                    <div className="emp-profile__grid">
                      <Fact label="Date of birth" value={employee.date_of_birth} />
                      <Fact label="Gender" value={genderLabel(employee.gender)} />
                      <Fact label="Blood group" value={employee.blood_group} />
                      <Fact label="Mother language" value={employee.mother_language} />
                      <Fact
                        label="Languages known"
                        value={(employee.languages_known || []).join(', ')}
                      />
                    </div>
                  </article>
                </>
              )}
            </>
          ) : null}

          {activeTab === 'contact' ? (
            <>
              {editing ? (
                <form className="emp-profile__card emp-profile__card--edit" onSubmit={saveEmployee}>
                  <header className="emp-profile__card-head">
                    <div>
                      <h2>Edit contact details</h2>
                      <p>Update phone numbers, address, and emergency contact.</p>
                    </div>
                  </header>

                  <h3 className="emp-profile__section-title">Phone numbers</h3>
                  <div className="emp-profile__edit-grid">
                    <label className="field">
                      <span>Mobile number</span>
                      <input
                        value={editForm.mobile_number}
                        onChange={(e) => setEditForm({ ...editForm, mobile_number: e.target.value })}
                      />
                      {fieldErrors.mobile_number ? (
                        <em className="field-error">{fieldErrors.mobile_number}</em>
                      ) : null}
                    </label>
                    <label className="field">
                      <span>Alternate mobile</span>
                      <input
                        value={editForm.alternate_mobile}
                        onChange={(e) => setEditForm({ ...editForm, alternate_mobile: e.target.value })}
                      />
                    </label>
                  </div>

                  <h3 className="emp-profile__section-title">Address</h3>
                  <div className="emp-profile__edit-grid">
                    <label className="field emp-profile__span-2">
                      <span>Address line</span>
                      <input
                        value={editForm.address_line1}
                        onChange={(e) => setEditForm({ ...editForm, address_line1: e.target.value })}
                      />
                    </label>
                    <label className="field">
                      <span>City</span>
                      <input
                        value={editForm.city}
                        onChange={(e) => setEditForm({ ...editForm, city: e.target.value })}
                      />
                    </label>
                    <label className="field">
                      <span>State</span>
                      <input
                        value={editForm.state}
                        onChange={(e) => setEditForm({ ...editForm, state: e.target.value })}
                      />
                    </label>
                    <label className="field">
                      <span>Country</span>
                      <input
                        value={editForm.country}
                        onChange={(e) => setEditForm({ ...editForm, country: e.target.value })}
                      />
                    </label>
                    <label className="field">
                      <span>Postal code</span>
                      <input
                        value={editForm.postal_code}
                        onChange={(e) => setEditForm({ ...editForm, postal_code: e.target.value })}
                      />
                    </label>
                  </div>

                  <h3 className="emp-profile__section-title">Emergency contact</h3>
                  <div className="emp-profile__edit-grid">
                    <label className="field">
                      <span>Contact name</span>
                      <input
                        value={editForm.emergency_contact_name}
                        onChange={(e) =>
                          setEditForm({ ...editForm, emergency_contact_name: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      <span>Relationship</span>
                      <input
                        value={editForm.emergency_contact_relationship}
                        onChange={(e) =>
                          setEditForm({ ...editForm, emergency_contact_relationship: e.target.value })
                        }
                        placeholder="Spouse, Parent, Sibling…"
                      />
                    </label>
                    <label className="field">
                      <span>Phone</span>
                      <input
                        value={editForm.emergency_contact_phone}
                        onChange={(e) =>
                          setEditForm({ ...editForm, emergency_contact_phone: e.target.value })
                        }
                      />
                      {fieldErrors.emergency_contact_phone ? (
                        <em className="field-error">{fieldErrors.emergency_contact_phone}</em>
                      ) : null}
                    </label>
                  </div>

                  <FormSaveBar saving={saving} onCancel={cancelEditing} />
                </form>
              ) : (
                <>
                  <article className="emp-profile__card">
                    <header className="emp-profile__card-head emp-profile__card-head--row">
                      <div>
                        <h2>Contact & address</h2>
                        <p>Phone numbers and location details.</p>
                      </div>
                      <Button type="button" variant="secondary" onClick={startEditing}>
                        Edit
                      </Button>
                    </header>
                    <div className="emp-profile__grid">
                      <Fact label="Mobile number" value={employee.mobile_number} />
                      <Fact label="Alternate mobile" value={employee.alternate_mobile} />
                      <Fact label="Address" value={employee.address_line1} />
                      <Fact label="City" value={employee.city} />
                      <Fact label="State" value={employee.state} />
                      <Fact label="Country" value={employee.country} />
                      <Fact label="Postal code" value={employee.postal_code} />
                    </div>
                  </article>

                  <article className="emp-profile__card">
                    <header className="emp-profile__card-head emp-profile__card-head--row">
                      <div>
                        <h2>Emergency contact</h2>
                        <p>Who to reach in case of an emergency.</p>
                      </div>
                      <Button type="button" variant="secondary" onClick={startEditing}>
                        Edit
                      </Button>
                    </header>
                    <div className="emp-profile__grid">
                      <Fact label="Name" value={employee.emergency_contact_name} />
                      <Fact label="Relationship" value={employee.emergency_contact_relationship} />
                      <Fact label="Phone" value={employee.emergency_contact_phone} />
                    </div>
                  </article>
                </>
              )}
            </>
          ) : null}

          {activeTab === 'bank' ? (
            <>
              {editing ? (
                <form className="emp-profile__card emp-profile__card--edit" onSubmit={saveEmployee}>
                  <header className="emp-profile__card-head emp-profile__card-head--row">
                    <div>
                      <h2>Edit bank details</h2>
                      <p>Manage salary accounts used for payroll transfers.</p>
                    </div>
                    <Button type="button" variant="secondary" onClick={addBankRow}>
                      Add account
                    </Button>
                  </header>

                  {fieldErrors.bank_details ? (
                    <em className="field-error">{fieldErrors.bank_details}</em>
                  ) : null}

                  <div className="emp-bank__list">
                    {editForm.bank_details.map((row, index) => (
                      <div
                        key={index}
                        className={`emp-bank__card emp-bank__card--edit ${row.is_primary ? 'is-primary' : ''}`}
                      >
                        <div className="emp-bank__card-top">
                          <div className="emp-bank__brand">
                            <span className="emp-bank__mark" aria-hidden>
                              {bankInitials(row.bank_name)}
                            </span>
                            <div>
                              <strong>Account {index + 1}</strong>
                              <em>{row.bank_name || 'New bank account'}</em>
                            </div>
                          </div>
                          <div className="emp-bank__card-tools">
                            <label className={`emp-bank__primary-toggle ${row.is_primary ? 'is-on' : ''}`}>
                              <input
                                type="radio"
                                name="primary-bank"
                                checked={row.is_primary}
                                onChange={() => setPrimaryBank(index)}
                              />
                              <span>{row.is_primary ? 'Primary' : 'Set primary'}</span>
                            </label>
                            <Button type="button" variant="ghost" onClick={() => removeBankRow(index)}>
                              Remove
                            </Button>
                          </div>
                        </div>

                        <div className="emp-profile__edit-grid">
                          <label className="field">
                            <span>Account holder name</span>
                            <input
                              value={row.account_holder_name}
                              onChange={(e) =>
                                updateBankRow(index, { account_holder_name: e.target.value })
                              }
                              placeholder="Name as on bank records"
                            />
                          </label>
                          <label className="field">
                            <span>Bank name</span>
                            <input
                              value={row.bank_name}
                              onChange={(e) => updateBankRow(index, { bank_name: e.target.value })}
                              placeholder="e.g. HDFC Bank"
                            />
                          </label>
                          <label className="field">
                            <span>Account number</span>
                            <input
                              value={row.account_number}
                              onChange={(e) =>
                                updateBankRow(index, {
                                  account_number: e.target.value.replace(/\s+/g, ''),
                                })
                              }
                              inputMode="numeric"
                              placeholder="Enter account number"
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
                              onChange={(e) =>
                                updateBankRow(index, { ifsc_code: e.target.value.toUpperCase() })
                              }
                              placeholder="HDFC0001234"
                              maxLength={11}
                            />
                            {fieldErrors[`bank_details.${index}.ifsc_code`] ? (
                              <em className="field-error">
                                {fieldErrors[`bank_details.${index}.ifsc_code`]}
                              </em>
                            ) : null}
                          </label>
                        </div>
                      </div>
                    ))}

                    {!editForm.bank_details.length ? (
                      <div className="emp-bank__empty">
                        <strong>No accounts yet</strong>
                        <p>Add at least one salary account for payroll transfers.</p>
                        <Button type="button" variant="secondary" onClick={addBankRow}>
                          Add bank account
                        </Button>
                      </div>
                    ) : null}
                  </div>

                  <FormSaveBar saving={saving} onCancel={cancelEditing} />
                </form>
              ) : (
                <article className="emp-profile__card emp-bank">
                  <header className="emp-profile__card-head emp-profile__card-head--row">
                    <div>
                      <h2>Bank details</h2>
                      <p>Salary accounts used for payroll transfers.</p>
                    </div>
                    <div className="emp-profile__edit-actions">
                      {(employee.bank_details || []).length ? (
                        <Button
                          type="button"
                          variant={bankRevealed ? 'ghost' : 'secondary'}
                          onClick={() => setBankRevealed((prev) => !prev)}
                        >
                          {bankRevealed ? 'Hide numbers' : 'Show numbers'}
                        </Button>
                      ) : null}
                      <Button type="button" variant="secondary" onClick={startEditing}>
                        Edit
                      </Button>
                    </div>
                  </header>

                  {(employee.bank_details || []).length ? (
                    <div className="emp-bank__view">
                      <div className="emp-bank__summary" aria-label="Bank summary">
                        <div className="emp-bank__stat">
                          <span>Accounts</span>
                          <strong>{employee.bank_details!.length}</strong>
                        </div>
                        <div className="emp-bank__stat emp-bank__stat--accent">
                          <span>Primary bank</span>
                          <strong>
                            {employee.bank_details!.find((row) => row.is_primary)?.bank_name ||
                              employee.bank_details![0]?.bank_name ||
                              '—'}
                          </strong>
                        </div>
                        <div className="emp-bank__stat">
                          <span>Primary holder</span>
                          <strong>
                            {employee.bank_details!.find((row) => row.is_primary)?.account_holder_name ||
                              employee.bank_details![0]?.account_holder_name ||
                              '—'}
                          </strong>
                        </div>
                      </div>

                      <div className="emp-bank__list">
                        {employee.bank_details!.map((row, index) => (
                          <div
                            key={row.id || index}
                            className={`emp-bank__card ${row.is_primary ? 'is-primary' : ''}`}
                          >
                            <div className="emp-bank__card-top">
                              <div className="emp-bank__brand">
                                <span className="emp-bank__mark" aria-hidden>
                                  {bankInitials(row.bank_name)}
                                </span>
                                <div>
                                  <strong>{row.bank_name || 'Bank account'}</strong>
                                  <em>{row.account_holder_name || 'Account holder not set'}</em>
                                </div>
                              </div>
                              {row.is_primary ? (
                                <span className="emp-bank__badge">Primary</span>
                              ) : (
                                <span className="emp-bank__badge emp-bank__badge--muted">
                                  Account {index + 1}
                                </span>
                              )}
                            </div>

                            <div className="emp-bank__number">
                              <span>Account number</span>
                              <strong>
                                {bankRevealed
                                  ? formatAccountNumber(row.account_number)
                                  : maskAccountNumber(row.account_number)}
                              </strong>
                            </div>

                            <div className="emp-bank__meta">
                              <div>
                                <span>IFSC</span>
                                <strong>{row.ifsc_code || '—'}</strong>
                              </div>
                              <div>
                                <span>Holder</span>
                                <strong>{row.account_holder_name || '—'}</strong>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="emp-bank__empty">
                      <strong>No bank accounts on file</strong>
                      <p>Add a bank account to enable payroll transfers.</p>
                      <Button type="button" variant="secondary" onClick={startEditing}>
                        Add bank account
                      </Button>
                    </div>
                  )}
                </article>
              )}
            </>
          ) : null}

          {activeTab === 'tax' ? (
            <>
              {editing ? (
                <form className="emp-profile__card emp-profile__card--edit" onSubmit={saveEmployee}>
                  <header className="emp-profile__card-head">
                    <div>
                      <h2>Edit tax details</h2>
                      <p>PAN, statutory IDs, and payroll tax applicability.</p>
                    </div>
                  </header>

                  {fieldErrors.tax_detail ? (
                    <em className="field-error">{fieldErrors.tax_detail}</em>
                  ) : null}

                  <div className="emp-profile__edit-grid">
                    <label className="field">
                      <span>PAN number</span>
                      <input
                        value={editForm.tax_detail.pan_number}
                        onChange={(e) =>
                          updateTaxDetail({ pan_number: e.target.value.toUpperCase() })
                        }
                        placeholder="ABCDE1234F"
                        maxLength={10}
                      />
                      {fieldErrors['tax_detail.pan_number'] ? (
                        <em className="field-error">{fieldErrors['tax_detail.pan_number']}</em>
                      ) : null}
                    </label>
                    <label className="field">
                      <span>Aadhaar number</span>
                      <input
                        value={editForm.tax_detail.aadhaar_number}
                        onChange={(e) =>
                          updateTaxDetail({
                            aadhaar_number: e.target.value.replace(/\D/g, '').slice(0, 12),
                          })
                        }
                        placeholder="12-digit Aadhaar"
                        maxLength={12}
                        inputMode="numeric"
                      />
                      {fieldErrors['tax_detail.aadhaar_number'] ? (
                        <em className="field-error">{fieldErrors['tax_detail.aadhaar_number']}</em>
                      ) : null}
                    </label>
                    <label className="field">
                      <span>UAN number</span>
                      <input
                        value={editForm.tax_detail.uan_number}
                        onChange={(e) =>
                          updateTaxDetail({ uan_number: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      <span>PF number</span>
                      <input
                        value={editForm.tax_detail.pf_number}
                        onChange={(e) =>
                          updateTaxDetail({ pf_number: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      <span>ESI number</span>
                      <input
                        value={editForm.tax_detail.esi_number}
                        onChange={(e) =>
                          updateTaxDetail({ esi_number: e.target.value })
                        }
                      />
                    </label>
                    <label className="field">
                      <span>Tax regime</span>
                      <select
                        value={editForm.tax_detail.tax_regime}
                        onChange={(e) =>
                          updateTaxDetail({ tax_regime: e.target.value })
                        }
                      >
                        <option value="new">New Regime</option>
                        <option value="old">Old Regime</option>
                      </select>
                      {fieldErrors['tax_detail.tax_regime'] || fieldErrors.tax_regime ? (
                        <em className="field-error">
                          {fieldErrors['tax_detail.tax_regime'] || fieldErrors.tax_regime}
                        </em>
                      ) : null}
                    </label>
                    <label className="field field--full">
                      <span>Tax identification number</span>
                      <input
                        value={editForm.tax_detail.tax_identification_number}
                        onChange={(e) =>
                          updateTaxDetail({ tax_identification_number: e.target.value })
                        }
                        placeholder="TIN / SSN / National tax ID"
                      />
                    </label>
                  </div>

                  <div className="emp-profile__edit-grid emp-tax__flags">
                    <label className="field field--check">
                      <input
                        type="checkbox"
                        checked={editForm.tax_detail.is_pf_applicable}
                        onChange={(e) =>
                          updateTaxDetail({ is_pf_applicable: e.target.checked })
                        }
                      />
                      <span>PF applicable</span>
                    </label>
                    <label className="field field--check">
                      <input
                        type="checkbox"
                        checked={editForm.tax_detail.is_esi_applicable}
                        onChange={(e) =>
                          updateTaxDetail({ is_esi_applicable: e.target.checked })
                        }
                      />
                      <span>ESI applicable</span>
                    </label>
                    <label className="field field--check">
                      <input
                        type="checkbox"
                        checked={editForm.tax_detail.professional_tax_applicable}
                        onChange={(e) =>
                          updateTaxDetail({ professional_tax_applicable: e.target.checked })
                        }
                      />
                      <span>Professional tax applicable</span>
                    </label>
                    <label className="field field--check">
                      <input
                        type="checkbox"
                        checked={editForm.tax_detail.labour_welfare_fund_applicable}
                        onChange={(e) =>
                          updateTaxDetail({ labour_welfare_fund_applicable: e.target.checked })
                        }
                      />
                      <span>Labour welfare fund applicable</span>
                    </label>
                  </div>

                  <FormSaveBar saving={saving} onCancel={cancelEditing} />
                </form>
              ) : (
                <article className="emp-profile__card">
                  <header className="emp-profile__card-head emp-profile__card-head--row">
                    <div>
                      <h2>Tax details</h2>
                      <p>Sensitive statutory IDs stay hidden until you choose to view them.</p>
                    </div>
                    <div className="emp-profile__edit-actions">
                      <Button
                        type="button"
                        variant={taxRevealed ? 'ghost' : 'secondary'}
                        onClick={() => setTaxRevealed((prev) => !prev)}
                      >
                        {taxRevealed ? 'Hide details' : 'View tax details'}
                      </Button>
                      <Button type="button" variant="secondary" onClick={startEditing}>
                        Edit
                      </Button>
                    </div>
                  </header>

                  {taxRevealed ? (
                    <div className="emp-profile__grid">
                      <Fact label="PAN" value={employee.tax_detail?.pan_number} />
                      <Fact label="Aadhaar" value={employee.tax_detail?.aadhaar_number} />
                      <Fact label="UAN" value={employee.tax_detail?.uan_number} />
                      <Fact label="PF number" value={employee.tax_detail?.pf_number} />
                      <Fact label="ESI number" value={employee.tax_detail?.esi_number} />
                      <Fact
                        label="Tax regime"
                        value={
                          employee.tax_detail?.tax_regime === 'old'
                            ? 'Old Regime'
                            : employee.tax_detail?.tax_regime === 'new'
                              ? 'New Regime'
                              : employee.tax_detail?.tax_regime
                        }
                      />
                      <Fact
                        label="Tax ID"
                        value={employee.tax_detail?.tax_identification_number}
                      />
                      <Fact
                        label="PF applicable"
                        value={employee.tax_detail?.is_pf_applicable ? 'Yes' : 'No'}
                      />
                      <Fact
                        label="ESI applicable"
                        value={employee.tax_detail?.is_esi_applicable ? 'Yes' : 'No'}
                      />
                      <Fact
                        label="Professional tax"
                        value={employee.tax_detail?.professional_tax_applicable ? 'Yes' : 'No'}
                      />
                      <Fact
                        label="Labour welfare fund"
                        value={employee.tax_detail?.labour_welfare_fund_applicable ? 'Yes' : 'No'}
                      />
                    </div>
                  ) : (
                    <div className="emp-tax__locked">
                      <strong>Tax details are hidden</strong>
                      <p>Click “View tax details” to reveal PAN, Aadhaar, and other statutory IDs.</p>
                    </div>
                  )}
                </article>
              )}
            </>
          ) : null}

          {activeTab === 'education' ? (
            <>
              {editing ? (
                <form className="emp-profile__card emp-profile__card--edit" onSubmit={saveEmployee}>
                  <header className="emp-profile__card-head">
                    <div>
                      <h2>Edit education details</h2>
                      <p>Manage academic qualifications on file.</p>
                    </div>
                  </header>

                  {fieldErrors.education_details ? (
                    <em className="field-error">{fieldErrors.education_details}</em>
                  ) : null}

                  <div className="emp-profile__repeat-list">
                    {editForm.education_details.map((row, index) => (
                      <div className="emp-profile__repeat-row" key={index}>
                        <div className="emp-profile__edit-grid">
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
                              onChange={(e) =>
                                updateEducationRow(index, { institution: e.target.value })
                              }
                            />
                          </label>
                          <label className="field">
                            <span>Field of study</span>
                            <input
                              value={row.field_of_study}
                              onChange={(e) =>
                                updateEducationRow(index, { field_of_study: e.target.value })
                              }
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
                              min={1950}
                              max={2100}
                            />
                            {fieldErrors[`education_details.${index}.year_of_passing`] ? (
                              <em className="field-error">
                                {fieldErrors[`education_details.${index}.year_of_passing`]}
                              </em>
                            ) : null}
                          </label>
                          <label className="field">
                            <span>Grade</span>
                            <input
                              value={row.grade}
                              onChange={(e) => updateEducationRow(index, { grade: e.target.value })}
                            />
                          </label>
                        </div>
                        <div className="emp-profile__repeat-actions">
                          <Button
                            type="button"
                            variant="ghost"
                            onClick={() => removeEducationRow(index)}
                          >
                            Remove entry
                          </Button>
                        </div>
                      </div>
                    ))}
                    {!editForm.education_details.length ? (
                      <p className="employees__empty-actions">No education entries added yet.</p>
                    ) : null}
                  </div>

                  <Button type="button" variant="secondary" onClick={addEducationRow}>
                    Add education entry
                  </Button>

                  <FormSaveBar saving={saving} onCancel={cancelEditing} />
                </form>
              ) : (
                <article className="emp-profile__card">
                  <header className="emp-profile__card-head emp-profile__card-head--row">
                    <div>
                      <h2>Education</h2>
                      <p>Academic path ordered by year of passing.</p>
                    </div>
                    <Button type="button" variant="secondary" onClick={startEditing}>
                      Edit
                    </Button>
                  </header>
                  {educationTree.length ? (
                    <ol className="education-tree" aria-label="Education timeline">
                      {educationTree.map((row, index) => {
                        const isLatest = index === educationTree.length - 1;
                        return (
                          <li
                            key={row.id || `${row.degree}-${row.year_of_passing}-${index}`}
                            className={[
                              'education-tree__item',
                              isLatest ? 'is-latest' : '',
                              row.year_of_passing == null ? 'is-unspecified' : '',
                            ]
                              .filter(Boolean)
                              .join(' ')}
                          >
                            <div className="education-tree__axis" aria-hidden>
                              <span className="education-tree__dot" />
                            </div>
                            <div className="education-tree__card">
                              <div className="education-tree__year">
                                {row.year_of_passing ?? 'Year not set'}
                              </div>
                              <strong className="education-tree__degree">
                                {row.degree || 'Qualification'}
                              </strong>
                              {row.institution ? (
                                <p className="education-tree__institution">{row.institution}</p>
                              ) : null}
                              <div className="education-tree__meta">
                                {row.field_of_study ? <span>{row.field_of_study}</span> : null}
                                {row.grade ? <span>Grade {row.grade}</span> : null}
                              </div>
                            </div>
                          </li>
                        );
                      })}
                    </ol>
                  ) : (
                    <div className="employees__empty-block">
                      <strong>No education details on file</strong>
                      <p>Add academic qualifications to complete this profile.</p>
                    </div>
                  )}
                </article>
              )}
            </>
          ) : null}

          {activeTab === 'experience' ? (
            <>
              {editing ? (
                <form className="emp-profile__card emp-profile__card--edit" onSubmit={saveEmployee}>
                  <header className="emp-profile__card-head">
                    <div>
                      <h2>Edit job experience</h2>
                      <p>Prior roles and companies outside the current organization.</p>
                    </div>
                  </header>

                  {fieldErrors.job_experiences ? (
                    <em className="field-error">{fieldErrors.job_experiences}</em>
                  ) : null}

                  <div className="emp-profile__repeat-list">
                    {editForm.job_experiences.map((row, index) => (
                      <div className="emp-profile__repeat-row" key={index}>
                        <div className="emp-profile__edit-grid">
                          <label className="field">
                            <span>Company</span>
                            <input
                              value={row.company_name}
                              onChange={(e) =>
                                updateExperienceRow(index, { company_name: e.target.value })
                              }
                            />
                          </label>
                          <label className="field">
                            <span>Job title</span>
                            <input
                              value={row.job_title}
                              onChange={(e) =>
                                updateExperienceRow(index, { job_title: e.target.value })
                              }
                            />
                          </label>
                          <label className="field">
                            <span>Start date</span>
                            <input
                              type="date"
                              value={row.start_date || ''}
                              onChange={(e) =>
                                updateExperienceRow(index, {
                                  start_date: e.target.value || null,
                                })
                              }
                            />
                            {fieldErrors[`job_experiences.${index}.start_date`] ? (
                              <em className="field-error">
                                {fieldErrors[`job_experiences.${index}.start_date`]}
                              </em>
                            ) : null}
                          </label>
                          <label className="field">
                            <span>End date</span>
                            <input
                              type="date"
                              value={row.end_date || ''}
                              onChange={(e) =>
                                updateExperienceRow(index, {
                                  end_date: e.target.value || null,
                                })
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
                              onChange={(e) =>
                                updateExperienceRow(index, { location: e.target.value })
                              }
                            />
                          </label>
                          <label className="emp-profile__check">
                            <input
                              type="checkbox"
                              checked={row.is_current}
                              onChange={(e) =>
                                updateExperienceRow(index, { is_current: e.target.checked })
                              }
                            />
                            <span>Currently working here</span>
                          </label>
                          <label className="field emp-profile__span-2">
                            <span>Description</span>
                            <textarea
                              rows={3}
                              value={row.description}
                              onChange={(e) =>
                                updateExperienceRow(index, { description: e.target.value })
                              }
                            />
                          </label>
                        </div>
                        <div className="emp-profile__repeat-actions">
                          <Button
                            type="button"
                            variant="ghost"
                            onClick={() => removeExperienceRow(index)}
                          >
                            Remove entry
                          </Button>
                        </div>
                      </div>
                    ))}
                    {!editForm.job_experiences.length ? (
                      <p className="employees__empty-actions">No experience entries added yet.</p>
                    ) : null}
                  </div>

                  <Button type="button" variant="secondary" onClick={addExperienceRow}>
                    Add experience entry
                  </Button>

                  <FormSaveBar saving={saving} onCancel={cancelEditing} />
                </form>
              ) : (
                <article className="emp-profile__card">
                  <header className="emp-profile__card-head emp-profile__card-head--row">
                    <div>
                      <h2>Experience</h2>
                      <p>Career snapshot with tenure and role breakdown.</p>
                    </div>
                    <Button type="button" variant="secondary" onClick={startEditing}>
                      Edit
                    </Button>
                  </header>
                  {experienceList.length ? (
                    <div className="experience-info">
                      <div className="experience-info__stats" aria-label="Experience summary">
                        <div className="experience-info__stat">
                          <span>Total tenure</span>
                          <strong>{experienceInsights.totalLabel}</strong>
                          <em>{experienceInsights.totalMonths} months tracked</em>
                        </div>
                        <div className="experience-info__stat">
                          <span>Roles</span>
                          <strong>{experienceInsights.roleCount}</strong>
                          <em>
                            {experienceInsights.companyCount}{' '}
                            {experienceInsights.companyCount === 1 ? 'company' : 'companies'}
                          </em>
                        </div>
                        <div className="experience-info__stat">
                          <span>Longest role</span>
                          <strong>{formatTenure(experienceInsights.longestMonths)}</strong>
                          <em>{experienceInsights.longestLabel}</em>
                        </div>
                        <div className="experience-info__stat experience-info__stat--accent">
                          <span>Now</span>
                          <strong>
                            {experienceInsights.currentTitle || 'No current role'}
                          </strong>
                          <em>
                            {experienceInsights.currentTitle
                              ? 'Marked as current'
                              : 'Add a current role if needed'}
                          </em>
                        </div>
                      </div>

                      <section className="experience-info__chart" aria-label="Tenure comparison">
                        <header className="experience-info__chart-head">
                          <h3>Tenure by role</h3>
                          <p>Bar length reflects months spent in each role.</p>
                        </header>
                        <ul className="experience-info__bars">
                          {experienceInsights.tenures.map(({ row, months }, index) => {
                            const width = Math.max(8, Math.round((months / experienceInsights.maxMonths) * 100));
                            const dates = experienceDateParts(row);
                            return (
                              <li
                                key={row.id || `${row.job_title}-${index}`}
                                className={row.is_current ? 'is-current' : undefined}
                              >
                                <div className="experience-info__bar-label">
                                  <strong>{row.job_title || 'Role'}</strong>
                                  <span>
                                    {formatTenure(months)} · {dates.start} – {dates.end}
                                  </span>
                                </div>
                                <div
                                  className="experience-info__bar-track"
                                  role="img"
                                  aria-label={`${row.job_title || 'Role'} tenure ${formatTenure(months)}`}
                                >
                                  <span
                                    className="experience-info__bar-fill"
                                    style={{ width: `${width}%` }}
                                  />
                                </div>
                              </li>
                            );
                          })}
                        </ul>
                      </section>

                      <ul className="experience-info__roles" aria-label="Role details">
                        {experienceInsights.tenures.map(({ row, months }, index) => {
                          const dates = experienceDateParts(row);
                          const mark = (row.company_name || row.job_title || 'E')
                            .trim()
                            .charAt(0)
                            .toUpperCase();
                          const share =
                            experienceInsights.totalMonths > 0
                              ? Math.round((months / experienceInsights.totalMonths) * 100)
                              : 0;
                          return (
                            <li
                              key={row.id || `detail-${row.company_name}-${index}`}
                              className={[
                                'experience-info__role',
                                row.is_current ? 'is-current' : '',
                              ]
                                .filter(Boolean)
                                .join(' ')}
                              style={{ animationDelay: `${0.05 + index * 0.05}s` }}
                            >
                              <div className="experience-info__role-mark" aria-hidden>
                                {mark}
                              </div>
                              <div className="experience-info__role-body">
                                <div className="experience-info__role-top">
                                  <div>
                                    <h3>{row.job_title || 'Role'}</h3>
                                    <p>
                                      {row.company_name || 'Company not set'}
                                      {row.location ? ` · ${row.location}` : ''}
                                    </p>
                                  </div>
                                  {row.is_current ? (
                                    <span className="experience-info__badge">Current</span>
                                  ) : null}
                                </div>
                                <div className="experience-info__metrics">
                                  <div>
                                    <span>Period</span>
                                    <strong>
                                      {dates.start} – {dates.end}
                                    </strong>
                                  </div>
                                  <div>
                                    <span>Tenure</span>
                                    <strong>{formatTenure(months)}</strong>
                                  </div>
                                  <div>
                                    <span>Share of career</span>
                                    <strong>{share}%</strong>
                                  </div>
                                </div>
                                {row.description ? (
                                  <p className="experience-info__desc">{row.description}</p>
                                ) : null}
                                <div className="experience-info__ring" aria-hidden>
                                  <svg viewBox="0 0 36 36">
                                    <circle className="experience-info__ring-bg" cx="18" cy="18" r="15.5" />
                                    <circle
                                      className="experience-info__ring-fg"
                                      cx="18"
                                      cy="18"
                                      r="15.5"
                                      style={{
                                        strokeDasharray: `${share}, 100`,
                                      }}
                                    />
                                  </svg>
                                  <em>{share}%</em>
                                </div>
                              </div>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ) : (
                    <div className="employees__empty-block">
                      <strong>No job experience on file</strong>
                      <p>Add prior roles to complete this profile.</p>
                    </div>
                  )}
                </article>
              )}
            </>
          ) : null}

          {activeTab === 'role' ? (
            <>
              {editing ? (
                <form className="emp-profile__card emp-profile__card--edit" onSubmit={saveEmployee}>
                  <header className="emp-profile__card-head">
                    <div>
                      <h2>Edit role details</h2>
                      <p>Update role, tenure, and record status.</p>
                    </div>
                  </header>

                  <div className="emp-profile__edit-grid">
                    <label className="field">
                      <span>Designation</span>
                      <select
                        value={editForm.designation_id}
                        onChange={(e) => setEditForm({ ...editForm, designation_id: e.target.value })}
                      >
                        <option value="">Select designation</option>
                        {(options?.designations || []).map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.department_name ? `${item.name} · ${item.department_name}` : item.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>Reporting manager</span>
                      <select
                        value={editForm.reporting_manager_id}
                        onChange={(e) =>
                          setEditForm({ ...editForm, reporting_manager_id: e.target.value })
                        }
                      >
                        <option value="">No manager assigned</option>
                        {managerOptions.map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.display_name}
                            {item.designation_name ? ` · ${item.designation_name}` : ''}
                          </option>
                        ))}
                      </select>
                      {fieldErrors.reporting_manager_id ? (
                        <em className="field-error">{fieldErrors.reporting_manager_id}</em>
                      ) : (
                        <em className="emp-profile__field-hint">Approves leave for this employee</em>
                      )}
                    </label>
                    <label className="field">
                      <span>Employee type</span>
                      <select
                        value={editForm.employee_type_id}
                        onChange={(e) => setEditForm({ ...editForm, employee_type_id: e.target.value })}
                      >
                        <option value="">Select type</option>
                        {(options?.employee_types || []).map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>Access type</span>
                      <select
                        value={editForm.access_type_id}
                        onChange={(e) => setEditForm({ ...editForm, access_type_id: e.target.value })}
                      >
                        <option value="">Select access</option>
                        {(options?.access_types || []).map((item) => (
                          <option key={item.id} value={item.id}>
                            {item.name}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="field">
                      <span>Joining date</span>
                      <input
                        type="date"
                        value={editForm.joining_date}
                        onChange={(e) => setEditForm({ ...editForm, joining_date: e.target.value })}
                      />
                    </label>
                    <label className="field">
                      <span>Exit date</span>
                      <input
                        type="date"
                        value={editForm.exit_date}
                        onChange={(e) => setEditForm({ ...editForm, exit_date: e.target.value })}
                      />
                    </label>
                    <label className="emp-profile__check">
                      <input
                        type="checkbox"
                        checked={editForm.is_active}
                        onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                      />
                      <span>Active record</span>
                    </label>
                  </div>

                  <FormSaveBar saving={saving} onCancel={cancelEditing} />
                </form>
              ) : (
                <article className="emp-profile__card">
                  <header className="emp-profile__card-head emp-profile__card-head--row">
                    <div>
                      <h2>Role</h2>
                      <p>Role identifiers and tenure for this organization.</p>
                    </div>
                    <Button type="button" variant="secondary" onClick={startEditing}>
                      Edit
                    </Button>
                  </header>
                  <div className="emp-profile__grid">
                    <Fact label="Designation" value={employee.designation_name} />
                    <Fact label="Reporting manager" value={employee.reporting_manager_name} />
                    <Fact label="Employee type" value={employee.employee_type_name} />
                    <Fact label="Access type" value={employee.access_type_name} />
                    <Fact label="Joining date" value={employee.joining_date} />
                    <Fact label="Exit date" value={employee.exit_date} />
                    <Fact label="Record status" value={employee.is_active ? 'Active' : 'Inactive'} />
                  </div>
                </article>
              )}
            </>
          ) : null}

          {activeTab === 'documents' ? (
            <EmployeeDocumentsPanel
              employeeId={employee.id}
              employeeTypeName={employee.employee_type_name}
            />
          ) : null}

          {activeTab === 'assets' ? <EmployeeAssetsPanel employeeId={employee.id} /> : null}

          {activeTab === 'attendance' && isOwnProfile ? (
            <EmployeeAttendancePanel employeeId={employee.id} />
          ) : null}

          {activeTab === 'activities' ? (
            <article className="emp-profile__card">
              <header className="emp-profile__card-head">
                <div>
                  <h2>Activities</h2>
                  <p>Immutable audit trail of lifecycle movements.</p>
                </div>
              </header>
              {(employee.history || []).length ? (
                <ul className="lifecycle-history">
                  {employee.history!.map((row) => (
                    <li key={row.id}>
                      <div>
                        <strong>
                          {row.from_status?.name || '—'} → {row.to_status.name}
                        </strong>
                        {row.remarks ? <p>{row.remarks}</p> : null}
                      </div>
                      <div className="lifecycle-history__meta">
                        <span>{row.changed_by_name || 'System'}</span>
                        <span>{new Date(row.changed_at).toLocaleString()}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="employees__empty-actions">No activity yet.</p>
              )}
            </article>
          ) : null}

          {activeTab === 'timeline' ? (
            <article className="emp-profile__card emp-timeline">
              <header className="emp-profile__card-head emp-profile__card-head--row">
                <div>
                  <h2>Lifecycle timeline</h2>
                  <p>Status journey with the date each step was reached.</p>
                </div>
                {timelineTotal ? (
                  <div className="emp-timeline__progress" aria-label="Lifecycle progress">
                    <span>
                      {timelineCompleted} of {timelineTotal}
                    </span>
                    <div className="emp-timeline__progress-track">
                      <div
                        className="emp-timeline__progress-fill"
                        style={{
                          width: `${Math.round((timelineCompleted / timelineTotal) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ) : null}
              </header>

              <div className="emp-timeline__layout">
                <ol className="lifecycle-timeline lifecycle-timeline--panel">
                  {timelineItems.map((item) => {
                    const time = formatTimelineTime(item.changedAt);
                    return (
                      <li
                        key={item.status.id}
                        data-lifecycle={lifecycleStatusTone(item.status)}
                        className={[
                          'lifecycle-timeline__item',
                          item.isCurrent ? 'is-current' : '',
                          item.isPast ? 'is-past' : '',
                          !item.changedAt && !item.isCurrent ? 'is-upcoming' : '',
                        ]
                          .filter(Boolean)
                          .join(' ')}
                      >
                        <span className="lifecycle-timeline__dot" aria-hidden />
                        <div className="lifecycle-timeline__body">
                          <div className="lifecycle-timeline__row">
                            <strong>{item.status.name}</strong>
                            {item.isCurrent ? <em>Current</em> : null}
                          </div>
                          <time
                            className="lifecycle-timeline__date"
                            dateTime={item.changedAt || undefined}
                          >
                            {formatTimelineDate(item.changedAt)}
                            {time ? <span>{time}</span> : null}
                          </time>
                        </div>
                      </li>
                    );
                  })}
                </ol>

                <aside className="emp-timeline__aside">
                  <div
                    className="emp-timeline__status-card"
                    data-lifecycle={lifecycleStatusTone(employee.lifecycle_status)}
                  >
                    <span>Current status</span>
                    <strong>{employee.lifecycle_status.name}</strong>
                    {employee.lifecycle_status.key === 'notice_period' ? (
                      <div className="emp-timeline__notice-meta">
                        <div>
                          <span>Notice started</span>
                          <strong>
                            {formatTimelineDate(
                              (employee.history || []).find((row) => row.to_status.key === 'notice_period')
                                ?.changed_at || null,
                            )}
                          </strong>
                        </div>
                        <div>
                          <span>Exit date</span>
                          <strong>
                            {employee.exit_date
                              ? formatTimelineDate(`${employee.exit_date}T00:00:00`)
                              : '—'}
                          </strong>
                        </div>
                        {organization?.notice_period_days ? (
                          <div>
                            <span>Notice period</span>
                            <strong>{organization.notice_period_days} days</strong>
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <p>Track and advance this employee through the organization lifecycle.</p>
                    )}
                  </div>

                  <div className="emp-timeline__actions">
                    <h3>Actions</h3>
                    <div className="employees__actions">
                      {(employee.available_transitions || []).length ? (
                        employee.available_transitions!.map((transition) => (
                          <div className="emp-timeline__action" key={transition.id}>
                            <span className="employees__rail-next">
                              Next: {transition.to_status.name}
                            </span>
                            <Button
                              onClick={() => openTransitionConfirm(transition)}
                              disabled={editing || Boolean(actionLoading)}
                            >
                              {transition.action_label || 'Continue'}
                            </Button>
                          </div>
                        ))
                      ) : (
                        <p className="employees__empty-actions">No further transitions.</p>
                      )}
                    </div>
                  </div>
                </aside>
              </div>
            </article>
          ) : null}

          {activeTab === 'leaves' ? <EmployeeLeavesPanel employeeId={employee.id} /> : null}
        </div>
      </div>

      <Modal
        open={Boolean(pendingTransition)}
        title="Confirm lifecycle update"
        onClose={closeTransitionConfirm}
        footer={
          <>
            <Button
              type="button"
              variant="ghost"
              onClick={closeTransitionConfirm}
              disabled={Boolean(actionLoading)}
            >
              Cancel
            </Button>
            <Button
              type="button"
              loading={Boolean(actionLoading)}
              onClick={() => {
                if (!pendingTransition) return;
                const needsExit = transitionNeedsExitDate(pendingTransition.to_status.key);
                if (needsExit && !transitionExitDate) {
                  setError(
                    pendingTransition.to_status.key === 'released'
                      ? 'Release date is required.'
                      : 'Exit date is required to start notice period.',
                  );
                  return;
                }
                void runTransition(
                  pendingTransition.to_status.id,
                  transitionRemarks,
                  needsExit ? transitionExitDate : undefined,
                );
              }}
            >
              {pendingTransition?.action_label || 'Confirm update'}
            </Button>
          </>
        }
      >
        {pendingTransition ? (
          <div className="emp-lifecycle-confirm">
            <p className="emp-lifecycle-confirm__lead">
              Move <strong>{employee.display_name}</strong> to the next lifecycle status?
              This will be recorded in the activity history.
            </p>

            <div className="emp-lifecycle-confirm__path" aria-label="Status change">
              <div
                className="emp-lifecycle-confirm__status"
                data-lifecycle={lifecycleStatusTone(employee.lifecycle_status)}
              >
                <span>From</span>
                <strong>{employee.lifecycle_status.name}</strong>
              </div>
              <span className="emp-lifecycle-confirm__arrow" aria-hidden>
                <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </span>
              <div
                className="emp-lifecycle-confirm__status emp-lifecycle-confirm__status--next"
                data-lifecycle={lifecycleStatusTone(pendingTransition.to_status)}
              >
                <span>To</span>
                <strong>{pendingTransition.to_status.name}</strong>
              </div>
            </div>

            {pendingTransition.to_status.key === 'notice_period' ? (
              <label className="emp-lifecycle-confirm__remarks">
                <span>
                  Exit date{' '}
                  <em>
                    (from {organization?.notice_period_days || '—'} day notice period)
                  </em>
                </span>
                <input
                  type="date"
                  value={transitionExitDate}
                  onChange={(e) => setTransitionExitDate(e.target.value)}
                  disabled={Boolean(actionLoading)}
                  required
                />
              </label>
            ) : null}

            {pendingTransition.to_status.key === 'released' ? (
              <label className="emp-lifecycle-confirm__remarks">
                <span>
                  Release / end date <em>(override if needed)</em>
                </span>
                <input
                  type="date"
                  value={transitionExitDate}
                  onChange={(e) => setTransitionExitDate(e.target.value)}
                  disabled={Boolean(actionLoading)}
                  required
                />
              </label>
            ) : null}

            <label className="emp-lifecycle-confirm__remarks">
              <span>Remarks <em>(optional)</em></span>
              <textarea
                value={transitionRemarks}
                onChange={(e) => setTransitionRemarks(e.target.value)}
                rows={3}
                placeholder="Add a note for this status change…"
                disabled={Boolean(actionLoading)}
              />
            </label>
          </div>
        ) : null}
      </Modal>
    </section>
  );
}
