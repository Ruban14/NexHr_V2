import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { MatCheckboxModule } from '@angular/material/checkbox';

import { AuthStore } from '../../../core/services/auth-store.service';
import { ButtonComponent } from '../../../shared/components/button/button.component';
import { CardComponent } from '../../../shared/components/card/card.component';
import { FormFieldComponent } from '../../../shared/components/form-field/form-field.component';
import { PasswordInputComponent } from '../../../shared/components/password-input/password-input.component';
import { APP_TIMEZONE } from '../../../shared/constants/timezone';
import {
  extractAccountLockedDetails,
  extractFieldErrors,
  getControlErrorMessage,
} from '../../../shared/utils/form.utils';
import { resolvePostAuthRedirect } from '../../../shared/utils/auth-navigation.utils';
import { formatAppDateTime } from '../../../shared/utils/datetime.utils';

interface LoginForm {
  email: FormControl<string | null>;
  password: FormControl<string | null>;
  rememberMe: FormControl<boolean | null>;
}

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
    MatCheckboxModule,
    CardComponent,
    ButtonComponent,
    FormFieldComponent,
    PasswordInputComponent,
  ],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss',
})
export class LoginComponent implements OnInit {
  readonly authStore = inject(AuthStore);
  private readonly route = inject(ActivatedRoute);

  readonly serverError = signal<string | null>(null);
  readonly infoMessage = signal<string | null>(null);
  readonly accountLocked = signal<ReturnType<typeof extractAccountLockedDetails>>(null);

  readonly lockedUntilLabel = computed(() => {
    const lockedUntil = this.accountLocked()?.lockedUntil;
    if (!lockedUntil) {
      return null;
    }

    return formatAppDateTime(lockedUntil, APP_TIMEZONE) ?? null;
  });

  readonly showForgotPasswordRecovery = computed(
    () => this.accountLocked()?.suggestForgotPassword === true,
  );

  readonly form = new FormGroup<LoginForm>({
    email: new FormControl('', {
      nonNullable: false,
      validators: [Validators.required, Validators.email],
    }),
    password: new FormControl('', {
      nonNullable: false,
      validators: [Validators.required],
    }),
    rememberMe: new FormControl(false),
  });

  ngOnInit(): void {
    if (this.route.snapshot.queryParamMap.get('verified') === '1') {
      this.infoMessage.set('Your email has been verified. Sign in to continue.');
    }
  }

  submit(): void {
    this.serverError.set(null);
    this.accountLocked.set(null);
    this.form.markAllAsTouched();

    if (this.form.invalid) {
      return;
    }

    const { email, password, rememberMe } = this.form.getRawValue();

    this.authStore
      .login(
        {
          email: email!.trim(),
          password: password!,
        },
        !!rememberMe,
      )
      .subscribe({
        next: () => {
          const returnUrl = resolvePostAuthRedirect(
            this.route.snapshot.queryParamMap.get('returnUrl'),
          );
          this.authStore.handleAuthSuccess('Welcome back.', returnUrl);
        },
        error: (error) => {
          const lockDetails = extractAccountLockedDetails(error);
          this.accountLocked.set(lockDetails);

          if (lockDetails?.suggestForgotPassword) {
            return;
          }

          const fieldErrors = extractFieldErrors(error);
          if (fieldErrors['email']) {
            this.serverError.set(fieldErrors['email']);
          } else if (fieldErrors['password']) {
            this.serverError.set(fieldErrors['password']);
          } else {
            this.serverError.set(this.authStore.handleAuthError(error, 'Unable to sign in.'));
          }
        },
      });
  }

  emailError(): string | null {
    return getControlErrorMessage(this.form.controls.email, 'Email');
  }

  passwordError(): string | null {
    return getControlErrorMessage(this.form.controls.password, 'Password');
  }
}
