import { Injectable, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, catchError, finalize, map, of, switchMap, tap, throwError } from 'rxjs';

import {
  ForgotPasswordRequest,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  ResetPasswordRequest,
  VerifyEmailRequest,
} from '../models/auth.model';
import { User, getUserFullName } from '../models/user.model';
import { AuthApiService } from './auth-api.service';
import { TokenStorageService } from './token-storage.service';
import { ToastService } from './toast.service';
import { extractErrorMessage, extractFieldErrors } from '../../shared/utils/form.utils';
import { resolvePostAuthRedirect } from '../../shared/utils/auth-navigation.utils';

export { extractErrorMessage, extractFieldErrors };

@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly authApi = inject(AuthApiService);
  private readonly tokenStorage = inject(TokenStorageService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);

  private readonly userSignal = signal<User | null>(null);
  private readonly bootstrappingSignal = signal(true);
  private readonly actionLoadingSignal = signal(false);

  readonly user = this.userSignal.asReadonly();
  readonly bootstrapping = this.bootstrappingSignal.asReadonly();
  readonly actionLoading = this.actionLoadingSignal.asReadonly();

  readonly isAuthenticated = computed(() => !!this.userSignal());
  readonly displayName = computed(() => {
    const user = this.userSignal();
    return user ? getUserFullName(user) : '';
  });

  bootstrap(): Observable<User | null> {
    this.bootstrappingSignal.set(true);

    if (!this.tokenStorage.getRefreshToken() && !this.tokenStorage.getAccessToken()) {
      this.bootstrappingSignal.set(false);
      return of(null);
    }

    return this.authApi.me().pipe(
      tap((user) => this.userSignal.set(user)),
      catchError(() => {
        const refreshToken = this.tokenStorage.getRefreshToken();
        if (!refreshToken) {
          this.clearSession(false);
          return of(null);
        }
        return this.refreshSession().pipe(
          switchMap((refreshed) => (refreshed ? this.authApi.me() : of(null))),
          tap((user) => this.userSignal.set(user)),
          catchError(() => {
            this.clearSession(false);
            return of(null);
          }),
        );
      }),
      finalize(() => this.bootstrappingSignal.set(false)),
    );
  }

  login(payload: LoginRequest, rememberMe: boolean): Observable<User> {
    this.actionLoadingSignal.set(true);
    return this.authApi.login(payload).pipe(
      tap((response) => this.establishSession(response, rememberMe)),
      map((response) => response.user),
      finalize(() => this.actionLoadingSignal.set(false)),
    );
  }

  establishSession(response: LoginResponse, rememberMe = true): void {
    this.tokenStorage.setTokens(response.tokens.access, response.tokens.refresh, rememberMe);
    this.userSignal.set(response.user);
  }

  register(payload: RegisterRequest): Observable<RegisterResponse> {
    this.actionLoadingSignal.set(true);
    return this.authApi.register(payload).pipe(
      tap(() => this.clearSession(false)),
      finalize(() => this.actionLoadingSignal.set(false)),
    );
  }

  logout(navigate = true): Observable<void> {
    const refreshToken = this.tokenStorage.getRefreshToken();
    this.actionLoadingSignal.set(true);

    const request$ = refreshToken
      ? this.authApi.logout({ refresh: refreshToken }).pipe(catchError(() => of(undefined)))
      : of(undefined);

    return request$.pipe(
      tap(() => this.clearSession(navigate)),
      finalize(() => this.actionLoadingSignal.set(false)),
    );
  }

  refreshSession(): Observable<boolean> {
    const refreshToken = this.tokenStorage.getRefreshToken();
    if (!refreshToken) {
      return of(false);
    }

    return this.authApi.refresh(refreshToken).pipe(
      tap((tokens) => {
        this.tokenStorage.setAccessToken(tokens.access);
        this.tokenStorage.setRefreshToken(tokens.refresh);
      }),
      map(() => true),
      catchError(() => {
        this.clearSession(false);
        return of(false);
      }),
    );
  }

  forgotPassword(payload: ForgotPasswordRequest): Observable<void> {
    this.actionLoadingSignal.set(true);
    return this.authApi.forgotPassword(payload).pipe(finalize(() => this.actionLoadingSignal.set(false)));
  }

  resetPassword(payload: ResetPasswordRequest): Observable<void> {
    this.actionLoadingSignal.set(true);
    return this.authApi.resetPassword(payload).pipe(finalize(() => this.actionLoadingSignal.set(false)));
  }

  verifyEmail(payload: VerifyEmailRequest): Observable<void> {
    this.actionLoadingSignal.set(true);
    return this.authApi.verifyEmail(payload).pipe(
      finalize(() => this.actionLoadingSignal.set(false)),
    );
  }

  resendVerification(email: string): Observable<void> {
    this.actionLoadingSignal.set(true);
    return this.authApi
      .resendVerification({ email })
      .pipe(finalize(() => this.actionLoadingSignal.set(false)));
  }

  reloadUser(): Observable<User> {
    return this.authApi.me().pipe(tap((user) => this.userSignal.set(user)));
  }

  clearSession(navigate = true): void {
    this.userSignal.set(null);
    this.tokenStorage.clear();
    if (navigate) {
      void this.router.navigate(['/auth/login']);
    }
  }

  handleAuthSuccess(message: string, redirectTo = '/app'): void {
    this.toast.success(message);
    void this.router.navigateByUrl(resolvePostAuthRedirect(redirectTo));
  }

  handleAuthError(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
    const message = extractErrorMessage(error, fallback);
    this.toast.error(message);
    return message;
  }
}
