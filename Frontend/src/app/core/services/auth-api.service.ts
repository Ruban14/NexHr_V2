import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';

import { API_CONFIG, authEndpoint } from '../config/api.config';
import { ApiResponse } from '../models/api.model';
import {
  ForgotPasswordRequest,
  LoginRequest,
  LoginResponse,
  LogoutRequest,
  RefreshResponse,
  RegisterRequest,
  RegisterResponse,
  ResendVerificationRequest,
  ResetPasswordRequest,
  VerifyEmailRequest,
} from '../models/auth.model';
import { User } from '../models/user.model';

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private readonly http = inject(HttpClient);
  private readonly apiConfig = inject(API_CONFIG);

  register(payload: RegisterRequest): Observable<RegisterResponse> {
    return this.http
      .post<ApiResponse<RegisterResponse>>(authEndpoint(this.apiConfig, '/register'), payload)
      .pipe(map((response) => this.unwrap(response)));
  }

  login(payload: LoginRequest): Observable<LoginResponse> {
    return this.http
      .post<ApiResponse<LoginResponse>>(authEndpoint(this.apiConfig, '/login'), payload)
      .pipe(map((response) => this.unwrap(response)));
  }

  logout(payload: LogoutRequest): Observable<void> {
    return this.http
      .post<ApiResponse<null>>(authEndpoint(this.apiConfig, '/logout'), payload)
      .pipe(map(() => undefined));
  }

  refresh(refreshToken: string): Observable<RefreshResponse> {
    return this.http
      .post<ApiResponse<RefreshResponse>>(authEndpoint(this.apiConfig, '/refresh'), {
        refresh: refreshToken,
      })
      .pipe(map((response) => this.unwrap(response)));
  }

  forgotPassword(payload: ForgotPasswordRequest): Observable<void> {
    return this.http
      .post<ApiResponse<null>>(authEndpoint(this.apiConfig, '/forgot-password'), payload)
      .pipe(map(() => undefined));
  }

  resetPassword(payload: ResetPasswordRequest): Observable<void> {
    return this.http
      .post<ApiResponse<null>>(authEndpoint(this.apiConfig, '/reset-password'), payload)
      .pipe(map(() => undefined));
  }

  verifyEmail(payload: VerifyEmailRequest): Observable<void> {
    return this.http
      .post<ApiResponse<null>>(authEndpoint(this.apiConfig, '/verify-email'), payload)
      .pipe(map(() => undefined));
  }

  resendVerification(payload: ResendVerificationRequest): Observable<void> {
    return this.http
      .post<ApiResponse<null>>(authEndpoint(this.apiConfig, '/resend-verification'), payload)
      .pipe(map(() => undefined));
  }

  me(): Observable<User> {
    return this.http
      .get<ApiResponse<User>>(authEndpoint(this.apiConfig, '/me'))
      .pipe(map((response) => this.unwrap(response)));
  }

  private unwrap<T>(response: ApiResponse<T>): T {
    if (!response.success || response.data === null) {
      throw response;
    }
    return response.data;
  }
}
