import { Component, inject } from '@angular/core';

import { AuthStore } from '../../../core/services/auth-store.service';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { BrandMarkComponent } from '../../../shared/components/brand-mark/brand-mark.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [BrandMarkComponent, ButtonComponent],
  templateUrl: './home.component.html',
  styleUrl: './home.component.scss',
})
export class HomeComponent {
  readonly authStore = inject(AuthStore);

  logout(): void {
    this.authStore.logout().subscribe();
  }
}
