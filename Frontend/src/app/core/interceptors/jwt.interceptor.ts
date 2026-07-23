import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { API_CONFIG } from '../config/api.config';
import { TokenStorageService } from '../services/token-storage.service';

const AUTH_SKIP_PATHS = [
  '/auth/login',
  '/auth/register',
  '/auth/refresh',
  '/auth/forgot-password',
  '/auth/reset-password',
  '/auth/verify-email',
  '/auth/resend-verification',
];

export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
  const tokenStorage = inject(TokenStorageService);
  const apiConfig = inject(API_CONFIG);

  const isApiRequest = req.url.startsWith(apiConfig.baseUrl);
  const shouldSkip = AUTH_SKIP_PATHS.some((path) => req.url.includes(path));

  if (!isApiRequest || shouldSkip) {
    return next(req);
  }

  const token = tokenStorage.getAccessToken();
  if (!token) {
    return next(req);
  }

  return next(
    req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    }),
  );
};
