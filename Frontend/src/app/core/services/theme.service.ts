import { Injectable, computed, signal } from '@angular/core';

export type ThemeMode = 'light' | 'dark' | 'system';

const THEME_STORAGE_KEY = 'nexhr_theme';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly preferenceSignal = signal<ThemeMode>(this.readStoredPreference());
  private readonly systemDark = signal(this.matchesSystemDark());

  readonly preference = this.preferenceSignal.asReadonly();
  readonly mode = computed<'light' | 'dark'>(() => {
    const pref = this.preferenceSignal();
    if (pref === 'system') {
      return this.systemDark() ? 'dark' : 'light';
    }
    return pref;
  });

  readonly preferenceLabel = computed(() => {
    const pref = this.preferenceSignal();
    if (pref === 'system') {
      return 'System';
    }
    return pref === 'dark' ? 'Dark' : 'Light';
  });

  constructor() {
    if (typeof window !== 'undefined') {
      const media = window.matchMedia('(prefers-color-scheme: dark)');
      media.addEventListener('change', () => {
        this.systemDark.set(media.matches);
        this.applyTheme();
      });
    }
    this.applyTheme();
  }

  setPreference(mode: ThemeMode): void {
    this.preferenceSignal.set(mode);
    localStorage.setItem(THEME_STORAGE_KEY, mode);
    this.applyTheme();
  }

  cyclePreference(): void {
    const order: ThemeMode[] = ['light', 'dark', 'system'];
    const current = this.preferenceSignal();
    const next = order[(order.indexOf(current) + 1) % order.length];
    this.setPreference(next);
  }

  private readStoredPreference(): ThemeMode {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored;
    }
    return 'system';
  }

  private matchesSystemDark(): boolean {
    if (typeof window === 'undefined') {
      return false;
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  private applyTheme(): void {
    if (typeof document === 'undefined') {
      return;
    }
    document.documentElement.setAttribute('data-theme', this.mode());
  }
}
