export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_email_verified: boolean;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface UserProfile extends User {}

export function getUserFullName(user: Pick<User, 'first_name' | 'last_name' | 'email' | 'full_name'>): string {
  const fromParts = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
  if (fromParts) {
    return fromParts;
  }
  if (user.full_name?.trim()) {
    return user.full_name.trim();
  }
  return user.email;
}
