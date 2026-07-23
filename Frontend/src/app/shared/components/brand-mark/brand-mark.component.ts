import { Component, input } from '@angular/core';

@Component({
  selector: 'app-brand-mark',
  standalone: true,
  templateUrl: './brand-mark.component.html',
  styleUrl: './brand-mark.component.scss',
})
export class BrandMarkComponent {
  readonly size = input<'sm' | 'md' | 'lg'>('md');
  readonly showWordmark = input(true);
  readonly tone = input<'default' | 'inverse'>('default');
}
