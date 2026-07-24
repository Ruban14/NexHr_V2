const ACCESS_KEY = 'nexhr_access_token';
const REFRESH_KEY = 'nexhr_refresh_token';
const REMEMBER_KEY = 'nexhr_remember_me';

function storage(rememberMe: boolean): Storage {
  return rememberMe ? localStorage : sessionStorage;
}

export const tokenStorage = {
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_KEY) ?? sessionStorage.getItem(ACCESS_KEY);
  },

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY) ?? sessionStorage.getItem(REFRESH_KEY);
  },

  isRememberMe(): boolean {
    return localStorage.getItem(REMEMBER_KEY) === '1';
  },

  setTokens(access: string, refresh: string, rememberMe: boolean): void {
    this.clear();
    const store = storage(rememberMe);
    store.setItem(ACCESS_KEY, access);
    store.setItem(REFRESH_KEY, refresh);
    if (rememberMe) {
      localStorage.setItem(REMEMBER_KEY, '1');
    }
  },

  setAccessToken(access: string): void {
    const rememberMe = this.isRememberMe();
    storage(rememberMe).setItem(ACCESS_KEY, access);
  },

  setRefreshToken(refresh: string): void {
    const rememberMe = this.isRememberMe();
    storage(rememberMe).setItem(REFRESH_KEY, refresh);
  },

  clear(): void {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(REMEMBER_KEY);
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
  },
};
