import { Component, inject, OnInit, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { AuthStore } from '../../../core/services/auth-store.service';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { CardComponent } from '../../../shared/components/card/card.component';
import { PasswordInputComponent } from '../../../shared/components/password-input/password-input.component';
import { PasswordStrengthComponent } from '../../../shared/components/password-strength/password-strength.component';
import {
  extractFieldErrors,
  getControlErrorMessage,
  getFormErrorMessage,
  passwordMatchValidator,
} from '../../../shared/utils/form.utils';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    CardComponent,
    ButtonComponent,
    PasswordInputComponent,
    PasswordStrengthComponent,
  ],
  templateUrl: './reset-password.component.html',
  styleUrl: './reset-password.component.scss',
})
export class ResetPasswordComponent implements OnInit {
  private readonly authStore = inject(AuthStore);
  private readonly route = inject(ActivatedRoute);

  readonly actionLoading = this.authStore.actionLoading;
  readonly serverError = signal<string | null>(null);
  readonly token = signal<string | null>(null);

  readonly form = new FormGroup(
    {
      password: new FormControl('', [Validators.required, Validators.minLength(9)]),
      password_confirm: new FormControl('', [Validators.required]),
    },
    { validators: passwordMatchValidator() },
  );

  ngOnInit(): void {
    const token = this.route.snapshot.queryParamMap.get('token');
    this.token.set(token);
    if (!token) {
      this.serverError.set('Reset link is invalid or missing. Request a new password reset email.');
    }
  }

  submit(): void {
    this.serverError.set(null);
    this.form.markAllAsTouched();

    const token = this.token();
    if (!token || this.form.invalid) {
      return;
    }

    const { password, password_confirm } = this.form.getRawValue();

    this.authStore
      .resetPassword({
        token,
        password: password!,
      })
      .subscribe({
        next: () => {
          this.authStore.handleAuthSuccess('Password updated. You can sign in now.', '/auth/login');
        },
        error: (error) => {
          const fieldErrors = extractFieldErrors(error);
          this.serverError.set(
            fieldErrors['token'] ??
              fieldErrors['password'] ??
              this.authStore.handleAuthError(error, 'Unable to reset password.'),
          );
        },
      });
  }

  fieldError(control: FormControl<string | null>, label: string): string | null {
    return getControlErrorMessage(control, label);
  }

  formError(): string | null {
    return getFormErrorMessage(this.form.errors);
  }
}
