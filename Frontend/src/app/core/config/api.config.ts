import { InjectionToken } from '@angular/core';

export interface ApiConfig {
  baseUrl: string;
  authPath: string;
}

export const API_CONFIG = new InjectionToken<ApiConfig>('API_CONFIG', {
  providedIn: 'root',
  factory: (): ApiConfig => ({
    baseUrl: 'http://localhost:8000/api',
    authPath: '/auth',
  }),
});

export function authEndpoint(config: ApiConfig, path: string): string {
  return `${config.baseUrl}${config.authPath}${path}`;
}
