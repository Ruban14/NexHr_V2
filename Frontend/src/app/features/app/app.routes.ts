import { Routes } from '@angular/router';

import { authGuard } from '../../core/guards/auth.guard';

export const APP_ROUTES: Routes = [
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./home/home.component').then((m) => m.HomeComponent),
  },
];
