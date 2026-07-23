import { Component, input, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-password-input',
  standalone: true,
  imports: [ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule, MatIconModule],
  templateUrl: './password-input.component.html',
  styleUrl: './password-input.component.scss',
})
export class PasswordInputComponent {
  readonly label = input.required<string>();
  readonly control = input.required<FormControl<string | null>>();
  readonly placeholder = input('Enter your password');
  readonly error = input<string | null>(null);
  readonly autocomplete = input('current-password');
  readonly inputId = input('');

  readonly visible = signal(false);

  toggleVisibility(): void {
    this.visible.update((value) => !value);
  }
}
