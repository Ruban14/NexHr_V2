import { Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../../core/services/auth-store.service';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { CardComponent } from '../../../shared/components/card/card.component';
import { FormFieldComponent } from '../../../shared/components/form-field/form-field.component';
import { extractFieldErrors, getControlErrorMessage } from '../../../shared/utils/form.utils';

@Component({
  selector: 'app-forgot-password',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, CardComponent, ButtonComponent, FormFieldComponent],
  templateUrl: './forgot-password.component.html',
  styleUrl: './forgot-password.component.scss',
})
export class ForgotPasswordComponent {
  readonly authStore = inject(AuthStore);
  readonly serverError = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  readonly form = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
  });

  submit(): void {
    this.serverError.set(null);
    this.successMessage.set(null);
    this.form.markAllAsTouched();

    if (this.form.invalid) {
      return;
    }

    this.authStore.forgotPassword({ email: this.form.controls.email.value!.trim() }).subscribe({
      next: () => {
        this.successMessage.set(
          'If an account exists for that email, password reset instructions have been sent.',
        );
        this.form.reset();
      },
      error: (error) => {
        const fieldErrors = extractFieldErrors(error);
        this.serverError.set(
          fieldErrors['email'] ?? this.authStore.handleAuthError(error, 'Unable to process request.'),
        );
      },
    });
  }

  emailError(): string | null {
    return getControlErrorMessage(this.form.controls.email, 'Email');
  }
}
