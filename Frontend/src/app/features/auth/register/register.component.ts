import { Component, inject, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthStore } from '../../../core/services/auth-store.service';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { CardComponent } from '../../../shared/components/card/card.component';
import { FormFieldComponent } from '../../../shared/components/form-field/form-field.component';
import { PasswordInputComponent } from '../../../shared/components/password-input/password-input.component';
import { PasswordStrengthComponent } from '../../../shared/components/password-strength/password-strength.component';
import {
  extractFieldErrors,
  getControlErrorMessage,
  getFormErrorMessage,
  passwordMatchValidator,
} from '../../../shared/utils/form.utils';

interface RegisterForm {
  first_name: FormControl<string | null>;
  last_name: FormControl<string | null>;
  email: FormControl<string | null>;
  password: FormControl<string | null>;
  password_confirm: FormControl<string | null>;
}

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    CardComponent,
    ButtonComponent,
    FormFieldComponent,
    PasswordInputComponent,
    PasswordStrengthComponent,
  ],
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
})
export class RegisterComponent {
  readonly authStore = inject(AuthStore);
  private readonly router = inject(Router);
  readonly serverError = signal<string | null>(null);
  readonly submitted = signal(false);
  readonly registrationComplete = signal(false);
  readonly registeredEmail = signal<string | null>(null);

  readonly form = new FormGroup<RegisterForm>(
    {
      first_name: new FormControl('', [Validators.required, Validators.maxLength(150)]),
      last_name: new FormControl('', [Validators.required, Validators.maxLength(150)]),
      email: new FormControl('', [Validators.required, Validators.email]),
      password: new FormControl('', [Validators.required, Validators.minLength(9)]),
      password_confirm: new FormControl('', [Validators.required]),
    },
    { validators: passwordMatchValidator() },
  );

  submit(): void {
    this.serverError.set(null);
    this.submitted.set(true);
    this.form.markAllAsTouched();

    if (this.form.invalid) {
      return;
    }

    const value = this.form.getRawValue();

    this.authStore
      .register({
        first_name: value.first_name!.trim(),
        last_name: value.last_name!.trim(),
        email: value.email!.trim(),
        password: value.password!,
      })
      .subscribe({
        next: (response) => {
          this.registeredEmail.set(response.user.email);
          this.registrationComplete.set(true);
        },
        error: (error) => {
          const fieldErrors = extractFieldErrors(error);
          if (Object.keys(fieldErrors).length) {
            this.serverError.set(Object.values(fieldErrors)[0] ?? 'Unable to create account.');
          } else {
            this.serverError.set(this.authStore.handleAuthError(error, 'Unable to create account.'));
          }
        },
      });
  }

  fieldError(control: FormControl<string | null>, label: string): string | null {
    return getControlErrorMessage(control, label);
  }

  formError(): string | null {
    return getFormErrorMessage(this.form.errors);
  }

  goToLogin(): void {
    void this.router.navigate(['/auth/login']);
  }
}
