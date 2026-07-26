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
};

export type EmployeeBankDetail = {
  id?: string;
  account_holder_name: string;
  bank_name: string;
  account_number: string;
  ifsc_code: string;
  is_primary: boolean;
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
