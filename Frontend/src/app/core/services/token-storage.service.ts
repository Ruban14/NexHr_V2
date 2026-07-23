import { Injectable } from '@angular/core';

const REFRESH_TOKEN_KEY = 'nexhr_refresh_token';
const REMEMBER_ME_KEY = 'nexhr_remember_me';
const ACCESS_TOKEN_KEY = 'nexhr_access_token';

@Injectable({ providedIn: 'root' })
export class TokenStorageService {
  private memoryAccessToken: string | null = null;

  setRememberMe(remember: boolean): void {
    sessionStorage.setItem(REMEMBER_ME_KEY, remember ? '1' : '0');
  }

  getRememberMe(): boolean {
    return sessionStorage.getItem(REMEMBER_ME_KEY) === '1';
  }

  setAccessToken(token: string | null): void {
    if (this.getRememberMe() && token) {
      sessionStorage.setItem(ACCESS_TOKEN_KEY, token);
      this.memoryAccessToken = null;
      return;
    }

    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    this.memoryAccessToken = token;
  }

  getAccessToken(): string | null {
    if (this.getRememberMe()) {
      return sessionStorage.getItem(ACCESS_TOKEN_KEY);
    }
    return this.memoryAccessToken;
  }

  setRefreshToken(token: string | null): void {
    if (token) {
      sessionStorage.setItem(REFRESH_TOKEN_KEY, token);
      return;
    }
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return sessionStorage.getItem(REFRESH_TOKEN_KEY);
  }

  setTokens(accessToken: string, refreshToken: string, rememberMe: boolean): void {
    this.setRememberMe(rememberMe);
    this.setAccessToken(accessToken);
    this.setRefreshToken(refreshToken);
  }

  clear(): void {
    this.memoryAccessToken = null;
    sessionStorage.removeItem(ACCESS_TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    sessionStorage.removeItem(REMEMBER_ME_KEY);
  }

  hasRefreshToken(): boolean {
    return !!this.getRefreshToken();
  }
}
