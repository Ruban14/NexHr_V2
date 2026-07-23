import { Component, input, output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

@Component({
  selector: 'app-button',
  standalone: true,
  imports: [MatButtonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './button.component.html',
  styleUrl: './button.component.scss',
  host: {
    '[class.nexhr-button--full-host]': 'fullWidth()',
  },
})
export class ButtonComponent {
  readonly type = input<'button' | 'submit'>('button');
  readonly variant = input<'primary' | 'secondary' | 'ghost' | 'danger' | 'success'>('primary');
  readonly size = input<'md' | 'lg'>('md');
  readonly fullWidth = input(false);
  readonly disabled = input(false);
  readonly loading = input(false);
  readonly ariaLabel = input<string | undefined>(undefined);
  readonly leadingIcon = input<string | undefined>(undefined);
  readonly trailingIcon = input<string | undefined>(undefined);

  readonly pressed = output<Event>();

  onClick(event: Event): void {
    if (this.disabled() || this.loading()) {
      event.preventDefault();
      event.stopPropagation();
      return;
    }
    this.pressed.emit(event);
  }
}
