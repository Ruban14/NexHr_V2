import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';

import { routeAnimations } from '../../core/animations/route.animations';
import { BrandMarkComponent } from '../../shared/components/brand-mark/brand-mark.component';

@Component({
  selector: 'app-auth-layout',
  standalone: true,
  imports: [RouterOutlet, BrandMarkComponent],
  templateUrl: './auth-layout.component.html',
  styleUrl: './auth-layout.component.scss',
  animations: [routeAnimations],
})
export class AuthLayoutComponent {
  private readonly router = inject(Router);

  readonly loginLayout = signal(this.isLoginRoute(this.router.url));

  constructor() {
    this.router.events
      .pipe(
        filter((event): event is NavigationEnd => event instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe((event) => {
        this.loginLayout.set(this.isLoginRoute(event.urlAfterRedirects));
      });
  }

  getRouteAnimation(outlet: RouterOutlet | null | undefined): string {
    if (!outlet?.isActivated) {
      return 'idle';
    }

    const animation = outlet.activatedRouteData?.['animation'];
    if (typeof animation === 'string' && animation.length > 0) {
      return animation;
    }

    return outlet.activatedRoute.snapshot.url.map((segment) => segment.path).join('/') || 'route';
  }

  private isLoginRoute(url: string): boolean {
    return (
      url.startsWith('/auth/login') ||
      url.startsWith('/auth/forgot-password') ||
      url.startsWith('/auth/reset-password')
    );
  }
}
