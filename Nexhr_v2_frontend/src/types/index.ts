export type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_email_verified: boolean;
  must_change_password: boolean;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
};

export type AuthTokens = {
  access: string;
  refresh: string;
};

export type LoginResponse = {
  user: User;
  tokens: AuthTokens;
};

export type RegisterResponse = {
  user: User;
};

export type IndustryType = {
  id: string;
  name: string;
  is_active: boolean;
};

export type OrganizationSetupStatus = {
  needs_setup: boolean;
  has_profile: boolean;
  has_membership: boolean;
  has_owned_organization: boolean;
};

export type OrganizationCreateRequest = {
  legal_name: string;
  display_name?: string;
  industry_type_id: string;
  organization_size?: string;
  email?: string;
  phone: string;
  website?: string;
  country?: string;
  state?: string;
  city?: string;
};

export type OrganizationCreateResponse = {
  organization: {
    id: string;
    organization_code: string;
    legal_name: string;
    display_name: string;
    email: string;
    phone: string;
    logo?: string;
  };
  membership: {
    id: string;
    employee_code: string;
    status: string;
  };
  profile: {
    id: string;
    display_name: string;
    profile_photo?: string;
  };
};

export type OrganizationBranch = {
  id: string;
  branch_code: string;
  branch_name: string;
  city: string;
  state: string;
  country: string;
  is_headquarters: boolean;
  status: string;
  organization_id: string;
};

export type BranchMembership = {
  id: string;
  organization_id: string;
  organization_name: string;
  organization_logo: string;
  branch_id: string;
  branch_code: string;
  branch_name: string;
  is_headquarters: boolean;
  employee_code: string;
  status: string;
  access_type_id: string | null;
  access_type_name: string | null;
  employee_type_id: string | null;
  employee_type_name: string | null;
  designation_id: string | null;
  designation_name: string | null;
};

export type Organization = {
  id: string;
  organization_code: string;
  legal_name: string;
  display_name: string;
  industry_type_id: string | null;
  industry_type_name: string | null;
  organization_size: string;
  email: string;
  phone: string;
  website: string;
  logo: string;
  country: string;
  state: string;
  city: string;
  timezone: string;
  currency: string;
  notice_period_days: number;
  is_active: boolean;
  owner_id: string;
  can_edit: boolean;
  current_branch?: OrganizationBranch;
  membership?: BranchMembership;
};

export type OrganizationUpdateRequest = {
  legal_name?: string;
  display_name?: string;
  industry_type_id?: string;
  organization_size?: string;
  email?: string;
  phone?: string;
  website?: string;
  logo?: string;
  country?: string;
  state?: string;
  city?: string;
  timezone?: string;
  currency?: string;
  notice_period_days?: number;
};

export type EmployeeBankDetail = {
  id?: string;
  account_holder_name: string;
  bank_name: string;
  account_number: string;
  ifsc_code: string;
  is_primary: boolean;
};

export type EmployeeTaxDetail = {
  id?: string;
  pan_number: string;
  aadhaar_number: string;
  uan_number: string;
  pf_number: string;
  esi_number: string;
  tax_regime: 'old' | 'new' | string;
  tax_identification_number: string;
  is_pf_applicable: boolean;
  is_esi_applicable: boolean;
  professional_tax_applicable: boolean;
  labour_welfare_fund_applicable: boolean;
};

export type EmployeeEducationDetail = {
  id?: string;
  degree: string;
  institution: string;
  field_of_study: string;
  year_of_passing: number | null;
  grade: string;
};

export type EmployeeJobExperience = {
  id?: string;
  company_name: string;
  job_title: string;
  start_date: string | null;
  end_date: string | null;
  is_current: boolean;
  location: string;
  description: string;
};

export type UserProfileDetail = {
  id: string;
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  display_name: string;
  profile_photo: string;
  mobile_number: string;
  alternate_mobile: string;
  emergency_contact_name: string;
  emergency_contact_relationship: string;
  emergency_contact_phone: string;
  bank_details: EmployeeBankDetail[];
  education_details: EmployeeEducationDetail[];
  job_experiences: EmployeeJobExperience[];
  date_of_birth: string | null;
  gender: string;
  blood_group: string;
  country: string;
  state: string;
  city: string;
  address_line1: string;
  postal_code: string;
  mother_language: string;
  languages_known: string[];
  is_profile_completed: boolean;
  employee_code: string | null;
  organization_id: string | null;
  organization_name: string | null;
  branch_id?: string | null;
  branch_name?: string | null;
  access_type_name?: string | null;
};

export type UserProfileUpdateRequest = {
  first_name?: string;
  last_name?: string;
  display_name?: string;
  profile_photo?: string;
  mobile_number?: string;
  alternate_mobile?: string;
  emergency_contact_name?: string;
  emergency_contact_relationship?: string;
  emergency_contact_phone?: string;
  bank_details?: EmployeeBankDetail[];
  education_details?: EmployeeEducationDetail[];
  job_experiences?: EmployeeJobExperience[];
  date_of_birth?: string | null;
  gender?: string;
  blood_group?: string;
  country?: string;
  state?: string;
  city?: string;
  address_line1?: string;
  postal_code?: string;
  mother_language?: string;
  languages_known?: string[];
};

export type PaginationMeta = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PaginatedResponse<T> = {
  items: T[];
  pagination: PaginationMeta;
};

export type MasterRecord = {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  description?: string;
  organization_id?: string;
  start_time?: string;
  end_time?: string;
  working_days?: number[];
};

export type Department = MasterRecord & {
  organization_id: string;
};

export type Designation = MasterRecord & {
  department_id: string;
  parent_id: string | null;
  sort_order: number;
  children?: Designation[];
};

export type EmployeeType = MasterRecord;

export type AccessType = MasterRecord & {
  description: string;
  industry_type_id: string | null;
};

export type Shift = MasterRecord & {
  organization_id: string;
  start_time: string;
  end_time: string;
};

export type WorkWeek = MasterRecord & {
  organization_id: string;
  working_days: number[];
};

export type LeaveType = MasterRecord & {
  organization_id: string;
};

export type HolidayCalendar = MasterRecord & {
  organization_id: string;
  year: number;
};

export type Holiday = {
  id: string;
  name: string;
  date: string;
  holiday_calendar_id: string;
  created_at: string;
  updated_at: string;
};

export type DocumentCategory = {
  id: string;
  name: string;
  description: string;
  display_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type DocumentDefinition = {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  organization_id: string | null;
  category_id: string;
  category_name: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentPolicyItem = {
  id?: string;
  document_id: string;
  document_name?: string | null;
  category_id?: string | null;
  category_name?: string | null;
  display_order: number;
  is_required: boolean;
  allow_multiple: boolean;
  verification_required: boolean;
  requires_expiry: boolean;
};

export type DocumentPolicy = {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
  is_active: boolean;
  organization_id: string;
  employee_type_id: string;
  employee_type_name: string | null;
  item_count: number;
  items: DocumentPolicyItem[];
  created_at: string;
  updated_at: string;
};

export type EmployeeDocumentRecord = {
  id: string;
  employee_id: string;
  document_id: string;
  document_name: string | null;
  category_id: string | null;
  category_name: string | null;
  file_id: string;
  file_name: string | null;
  file_url: string;
  file_size: number;
  mime_type: string;
  issue_date: string | null;
  expiry_date: string | null;
  status: 'pending' | 'approved' | 'rejected' | string;
  remarks: string;
  verified_by_id: string | null;
  verified_by_name: string | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DocumentComplianceItem = {
  policy_item_id: string;
  document_id: string;
  document_name: string;
  category_name: string | null;
  is_required: boolean;
  allow_multiple: boolean;
  verification_required: boolean;
  requires_expiry: boolean;
  display_order: number;
  status: 'missing' | 'optional_missing' | 'pending' | 'approved' | 'expired' | 'rejected' | string;
  latest_document: EmployeeDocumentRecord | null;
  upload_count: number;
};

export type DocumentCompliance = {
  policy: {
    id: string;
    name: string;
    description: string;
    is_default: boolean;
    employee_type_id: string;
    employee_type_name: string | null;
  } | null;
  overall_status: 'compliant' | 'incomplete' | 'pending_review' | 'no_policy' | string;
  message: string;
  summary: {
    required: number;
    approved: number;
    pending: number;
    missing: number;
    expired: number;
    rejected: number;
    optional: number;
  };
  items: DocumentComplianceItem[];
  pending: EmployeeDocumentRecord[];
  uploads: EmployeeDocumentRecord[];
};

export type AssetType = {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  organization_id: string;
  created_at: string;
  updated_at: string;
};

export type AssetStatus = 'available' | 'assigned' | 'lost' | 'damaged' | 'retired';

export type AssetRecord = {
  id: string;
  organization_id: string;
  asset_type_id: string;
  asset_type_name: string | null;
  asset_code: string;
  name: string;
  brand: string;
  model: string;
  serial_number: string;
  purchase_date: string | null;
  warranty_expiry: string | null;
  status: AssetStatus | string;
  remarks: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AssetAssignmentStatus = 'active' | 'returned' | 'lost';

export type EmployeeAssetAssignment = {
  id: string;
  organization_id: string;
  employee_id: string;
  asset_id: string;
  asset_code: string | null;
  asset_name: string | null;
  asset_type_name: string | null;
  serial_number: string | null;
  assigned_at: string | null;
  expected_return_at: string | null;
  returned_at: string | null;
  issued_by_id: string | null;
  issued_by_name: string | null;
  received_by_id: string | null;
  received_by_name: string | null;
  status: AssetAssignmentStatus | string;
  remarks: string;
  created_at: string;
  updated_at: string;
};

export type LeaveAllocationFrequency = 'yearly' | 'monthly' | 'quarterly';

export type LeavePolicyRule = {
  id?: string;
  leave_type_id: string;
  leave_type_name?: string | null;
  allocation_frequency: LeaveAllocationFrequency | string;
  allocation_quantity: string;
  annual_limit: string;
  carry_forward_allowed: boolean;
  carry_forward_limit: string;
  encashment_allowed: boolean;
  encashment_limit: string;
  allow_half_day: boolean;
  allow_negative_balance: boolean;
  minimum_service_days: number;
  maximum_consecutive_days: number | null;
  is_active: boolean;
};

export type LeavePolicy = {
  id: string;
  organization_id: string;
  employee_type_id: string;
  employee_type_name: string | null;
  code: string;
  name: string;
  description: string;
  effective_from: string | null;
  effective_to: string | null;
  is_default: boolean;
  is_active: boolean;
  rule_count: number;
  rules: LeavePolicyRule[];
  created_at: string;
  updated_at: string;
};

export type EmployeeLeaveBalance = {
  id: string;
  organization_id: string;
  employee_id: string;
  leave_type_id: string;
  leave_type_name: string | null;
  allocated: string;
  used: string;
  balance: string;
  created_at: string;
  updated_at: string;
};

export type LeaveApplicationStatus =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'cancelled';

export type LeaveApplication = {
  id: string;
  organization_id: string;
  employee_id: string;
  employee_name?: string | null;
  employee_code?: string | null;
  employee_designation_name?: string | null;
  leave_type_id: string;
  leave_type_name: string | null;
  from_date: string | null;
  to_date: string | null;
  number_of_days: string;
  is_half_day: boolean;
  reason: string;
  attachment_url: string | null;
  status: LeaveApplicationStatus | string;
  approved_by_id: string | null;
  approved_by_name: string | null;
  approved_at: string | null;
  remarks: string;
  expected_approver_id?: string | null;
  expected_approver_name?: string | null;
  can_review?: boolean;
  created_at: string;
  updated_at: string;
};

export type EmployeeLeaveLog = {
  id: string;
  organization_id: string;
  employee_id: string;
  leave_type_id: string;
  leave_type_name: string | null;
  transaction_type: string;
  quantity: string;
  balance_before: string;
  balance_after: string;
  leave_application_id: string | null;
  remarks: string;
  created_at: string;
  updated_at: string;
};

export type AttendanceStatus =
  | 'present'
  | 'absent'
  | 'half_day'
  | 'leave'
  | 'holiday'
  | 'week_off';

export type AttendanceBreak = {
  id: string;
  session_id: string;
  break_start: string | null;
  break_end: string | null;
  break_duration_hours: string | null;
  remarks: string;
  is_open: boolean;
  created_at: string;
  updated_at: string;
};

export type AttendanceSession = {
  id: string;
  attendance_id: string;
  check_in: string | null;
  check_out: string | null;
  worked_hours: string | null;
  source: string;
  remarks: string;
  is_open: boolean;
  breaks: AttendanceBreak[];
  created_at: string;
  updated_at: string;
  attendance_date?: string | null;
  attendance_status?: string | null;
  approval_status?: string | null;
  is_manual_day?: boolean;
  employee_id?: string;
  employee_name?: string | null;
  employee_code?: string | null;
};

export type AttendanceRecord = {
  id: string | null;
  organization_id: string;
  employee_id: string;
  employee_name?: string | null;
  employee_code?: string | null;
  employee_designation_name?: string | null;
  attendance_date: string | null;
  first_check_in: string | null;
  last_check_out: string | null;
  total_worked_hours: string | null;
  total_break_hours: string | null;
  overtime_hours: string | null;
  status: AttendanceStatus | string | null;
  is_manual?: boolean;
  approval_status?: string | null;
  approved_by_id?: string | null;
  approved_by_name?: string | null;
  approved_at?: string | null;
  approval_remarks?: string;
  expected_approver_id?: string | null;
  expected_approver_name?: string | null;
  can_review?: boolean;
  remarks: string;
  has_open_session: boolean;
  on_break: boolean;
  sessions: AttendanceSession[];
  created_at: string | null;
  updated_at: string | null;
};

export type AttendanceListResponse = {
  date: string;
  present_count: number;
  total_count: number;
  items: AttendanceRecord[];
};

export type LifecycleStatus = {
  id: string;
  name: string;
  key: string;
  ordinal: number;
  is_initial: boolean;
  is_terminal: boolean;
  is_active: boolean;
};

export type LifecycleTransition = {
  id: string;
  action_label: string;
  sort_order: number;
  from_status: LifecycleStatus;
  to_status: LifecycleStatus;
};

export type LifecycleHistoryEntry = {
  id: string;
  from_status: LifecycleStatus | null;
  to_status: LifecycleStatus;
  changed_by_id: string | null;
  changed_by_name: string | null;
  changed_at: string;
  remarks: string;
};

export type EmployeeMasterOption = {
  id: string;
  name: string;
  department_name?: string;
};

export type EmployeeRecord = {
  id: string;
  organization_id: string;
  branch_id: string | null;
  user_id: string | null;
  employee_code: string;
  email: string;
  first_name: string;
  last_name: string;
  display_name: string;
  profile_photo?: string;
  mobile_number?: string;
  alternate_mobile?: string;
  emergency_contact_name?: string;
  emergency_contact_relationship?: string;
  emergency_contact_phone?: string;
  bank_details?: EmployeeBankDetail[];
  education_details?: EmployeeEducationDetail[];
  job_experiences?: EmployeeJobExperience[];
  tax_detail?: EmployeeTaxDetail;
  date_of_birth?: string | null;
  gender?: string;
  blood_group?: string;
  country?: string;
  state?: string;
  city?: string;
  address_line1?: string;
  postal_code?: string;
  mother_language?: string;
  languages_known?: string[];
  joining_date: string | null;
  exit_date: string | null;
  is_active: boolean;
  designation_id: string | null;
  designation_name?: string | null;
  reporting_manager_id?: string | null;
  reporting_manager_name?: string | null;
  employee_type_id: string | null;
  employee_type_name?: string | null;
  access_type_id: string | null;
  access_type_name?: string | null;
  is_email_verified?: boolean;
  email_editable?: boolean;
  lifecycle_status: LifecycleStatus;
  available_transitions?: LifecycleTransition[];
  timeline_statuses?: LifecycleStatus[];
  history?: LifecycleHistoryEntry[];
  master_options?: {
    employee_types: EmployeeMasterOption[];
    access_types: EmployeeMasterOption[];
    designations: EmployeeMasterOption[];
  };
  created_at: string;
  updated_at: string;
};

export type EmployeeCreateRequest = {
  email: string;
  first_name?: string;
  last_name?: string;
  display_name?: string;
  designation_id?: string | null;
  employee_type_id?: string | null;
  access_type_id?: string | null;
  joining_date?: string | null;
};

export type MasterListParams = {
  search?: string;
  page?: number;
  page_size?: number;
  is_active?: boolean;
};

export function getUserFullName(user: Pick<User, 'first_name' | 'last_name' | 'email' | 'full_name'>): string {
  const fromParts = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
  if (fromParts) return fromParts;
  if (user.full_name?.trim()) return user.full_name.trim();
  return user.email;
}
