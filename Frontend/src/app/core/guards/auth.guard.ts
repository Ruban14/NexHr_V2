import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { map, of } from 'rxjs';

import { AuthStore } from '../services/auth-store.service';

export const authGuard: CanActivateFn = () => {
  const authStore = inject(AuthStore);
  const router = inject(Router);

  if (authStore.bootstrapping()) {
    return authStore.bootstrap().pipe(
      map((user) => {
        if (user) {
          return true;
        }
        return router.createUrlTree(['/auth/login'], {
          queryParams: { returnUrl: router.url },
        });
      }),
    );
  }

  if (authStore.isAuthenticated()) {
    return true;
  }

  return router.createUrlTree(['/auth/login'], {
    queryParams: { returnUrl: router.url },
  });
};

export const guestGuard: CanActivateFn = () => {
  const authStore = inject(AuthStore);
  const router = inject(Router);

  if (authStore.isAuthenticated()) {
    return router.createUrlTree(['/app']);
  }

  if (authStore.bootstrapping()) {
    return authStore.bootstrap().pipe(
      map((user) => (user ? router.createUrlTree(['/app']) : true)),
    );
  }

  return of(true);
};
