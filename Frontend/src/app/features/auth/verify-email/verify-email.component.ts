import { Component, inject, OnInit, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthStore } from '../../../core/services/auth-store.service';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { CardComponent } from '../../../shared/components/card/card.component';
import { FormFieldComponent } from '../../../shared/components/form-field/form-field.component';
import { getControlErrorMessage } from '../../../shared/utils/form.utils';

type VerifyState = 'idle' | 'verifying' | 'success' | 'error';

@Component({
  selector: 'app-verify-email',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, CardComponent, ButtonComponent, FormFieldComponent],
  templateUrl: './verify-email.component.html',
  styleUrl: './verify-email.component.scss',
})
export class VerifyEmailComponent implements OnInit {
  readonly authStore = inject(AuthStore);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly state = signal<VerifyState>('idle');
  readonly message = signal<string>('');

  readonly resendForm = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
  });

  ngOnInit(): void {
    const token = this.route.snapshot.queryParamMap.get('token');
    if (token) {
      this.verify(token);
    }
  }

  verify(token: string): void {
    this.state.set('verifying');
    this.authStore.verifyEmail({ token }).subscribe({
      next: () => {
        this.state.set('success');
        this.message.set('Your email has been verified. Redirecting you to sign in…');
        void this.router.navigate(['/auth/login'], {
          queryParams: { verified: '1' },
        });
      },
      error: (error) => {
        this.state.set('error');
        this.message.set(this.authStore.handleAuthError(error, 'Verification link is invalid or expired.'));
      },
    });
  }

  resend(): void {
    this.resendForm.markAllAsTouched();
    if (this.resendForm.invalid) {
      return;
    }

    this.authStore.resendVerification(this.resendForm.controls.email.value!.trim()).subscribe({
      next: () => {
        this.message.set('If an account exists for that email, a new verification link has been sent.');
      },
      error: (error) => {
        this.message.set(this.authStore.handleAuthError(error, 'Unable to resend verification email.'));
      },
    });
  }

  emailError(): string | null {
    return getControlErrorMessage(this.resendForm.controls.email, 'Email');
  }

  goToLogin(): void {
    void this.router.navigate(['/auth/login'], {
      queryParams: { verified: '1' },
    });
  }
}
