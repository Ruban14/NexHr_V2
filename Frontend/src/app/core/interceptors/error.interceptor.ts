import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, catchError, filter, switchMap, take, throwError } from 'rxjs';

import { API_CONFIG } from '../config/api.config';
import { AuthStore } from '../services/auth-store.service';
import { TokenStorageService } from '../services/token-storage.service';

let refreshInFlight = false;
let refreshSubject = new BehaviorSubject<string | null>(null);

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authStore = inject(AuthStore);
  const tokenStorage = inject(TokenStorageService);
  const router = inject(Router);
  const apiConfig = inject(API_CONFIG);

  const isApiRequest = req.url.startsWith(apiConfig.baseUrl);
  const isRefreshRequest = req.url.includes('/auth/refresh');

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (!isApiRequest) {
        return throwError(() => error);
      }

      if (error.status === 401 && !isRefreshRequest && tokenStorage.getRefreshToken()) {
        if (refreshInFlight) {
          return refreshSubject.pipe(
            filter((token): token is string => token !== null),
            take(1),
            switchMap((token) =>
              next(
                req.clone({
                  setHeaders: { Authorization: `Bearer ${token}` },
                }),
              ),
            ),
          );
        }

        refreshInFlight = true;
        refreshSubject = new BehaviorSubject<string | null>(null);

        return authStore.refreshSession().pipe(
          switchMap((refreshed) => {
            refreshInFlight = false;
            const newToken = tokenStorage.getAccessToken();
            if (!refreshed || !newToken) {
              refreshSubject.error(error);
              authStore.clearSession(true);
              return throwError(() => error);
            }
            refreshSubject.next(newToken);
            refreshSubject.complete();
            return next(
              req.clone({
                setHeaders: { Authorization: `Bearer ${newToken}` },
              }),
            );
          }),
          catchError((refreshError) => {
            refreshInFlight = false;
            refreshSubject.error(refreshError);
            authStore.clearSession(true);
            return throwError(() => refreshError);
          }),
        );
      }

      if (
        error.status === 401 &&
        !req.url.includes('/auth/login') &&
        (tokenStorage.getRefreshToken() || tokenStorage.getAccessToken())
      ) {
        authStore.clearSession(false);
        void router.navigate(['/auth/login'], {
          queryParams: { returnUrl: router.url },
        });
      }

      const body = error.error as { message?: string; errors?: unknown } | null;
      return throwError(() => ({
        status: error.status,
        message: body?.message ?? getDefaultMessage(error.status),
        errors: body?.errors ?? null,
      }));
    }),
  );
};

function getDefaultMessage(status: number): string {
  switch (status) {
    case 0:
      return 'Unable to reach the server. Check your connection.';
    case 403:
      return 'You do not have permission to perform this action.';
    case 404:
      return 'The requested resource was not found.';
    case 429:
      return 'Too many requests. Please wait and try again.';
    default:
      return 'An unexpected error occurred.';
  }
}
