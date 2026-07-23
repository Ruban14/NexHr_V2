import { Component, computed, input } from '@angular/core';

import { evaluatePasswordStrength } from '../../utils/form.utils';

@Component({
  selector: 'app-password-strength',
  standalone: true,
  templateUrl: './password-strength.component.html',
  styleUrl: './password-strength.component.scss',
})
export class PasswordStrengthComponent {
  readonly password = input('');

  readonly strength = computed(() => evaluatePasswordStrength(this.password()));

  readonly barWidth = computed(() => `${(this.strength().score / 5) * 100}%`);
}
