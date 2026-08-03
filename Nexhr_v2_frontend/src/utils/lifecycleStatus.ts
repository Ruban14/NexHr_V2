type LifecycleToneInput = {
  key?: string;
  is_initial?: boolean;
  is_terminal?: boolean;
};

export type LifecycleTone =
  | 'draft'
  | 'onboarding'
  | 'active'
  | 'notice'
  | 'released'
  | 'rehire'
  | 'neutral';

const KEY_TONES: Record<string, LifecycleTone> = {
  draft: 'draft',
  onboarding_started: 'onboarding',
  onboarding: 'onboarding',
  active: 'active',
  active_employee: 'active',
  notice_period: 'notice',
  notice: 'notice',
  released: 'released',
  exited: 'released',
  terminated: 'released',
  rehire: 'rehire',
};

export function lifecycleStatusTone(status?: LifecycleToneInput | null): LifecycleTone {
  if (!status) return 'neutral';
  const key = (status.key || '').trim().toLowerCase();
  if (key && KEY_TONES[key]) return KEY_TONES[key];
  if (status.is_terminal) return 'released';
  if (status.is_initial) return 'draft';
  return 'neutral';
}
