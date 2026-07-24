export type User = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_email_verified: boolean;
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
  code: string;
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
};

export type UserProfileUpdateRequest = {
  first_name?: string;
  last_name?: string;
  display_name?: string;
  profile_photo?: string;
  mobile_number?: string;
  alternate_mobile?: string;
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

export function getUserFullName(user: Pick<User, 'first_name' | 'last_name' | 'email' | 'full_name'>): string {
  const fromParts = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
  if (fromParts) return fromParts;
  if (user.full_name?.trim()) return user.full_name.trim();
  return user.email;
}
