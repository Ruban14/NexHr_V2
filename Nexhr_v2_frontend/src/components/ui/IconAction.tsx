import type { ButtonHTMLAttributes, ReactNode } from 'react';
import './IconAction.css';

type IconActionProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  label: string;
  danger?: boolean;
  success?: boolean;
  children: ReactNode;
};

/** Icon button with an immediate CSS tooltip. */
export function IconAction({
  label,
  danger = false,
  success = false,
  className = '',
  children,
  disabled,
  ...props
}: IconActionProps) {
  return (
    <button
      type="button"
      className={[
        'icon-action',
        danger ? 'icon-action--danger' : '',
        success ? 'icon-action--success' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      aria-label={label}
      data-tooltip={label}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}

export function IconAdd() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function IconEdit() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}

export function IconDelete() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M4 7h16" />
      <path d="M9 7V5h6v2" />
      <path d="M7 7l1 12h8l1-12" />
    </svg>
  );
}

export function IconMoveUp() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="m6 14 6-6 6 6" />
    </svg>
  );
}

export function IconMoveDown() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="m6 10 6 6 6-6" />
    </svg>
  );
}

/** Shown when record is active — click to deactivate. */
export function IconDeactivate() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <circle cx="12" cy="12" r="8" />
      <path d="M6.5 6.5 17.5 17.5" />
    </svg>
  );
}

/** Shown when record is inactive — click to activate. */
export function IconActivate() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <circle cx="12" cy="12" r="8" />
      <path d="m8.5 12.5 2.5 2.5 4.5-5" />
    </svg>
  );
}

export function IconApprove() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="m5 12 5 5L20 7" />
    </svg>
  );
}

export function IconReject() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M6 6 18 18M18 6 6 18" />
    </svg>
  );
}

export function IconView() {
  return (
    <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path d="M2.5 12S6.5 6 12 6s9.5 6 9.5 6-4 6-9.5 6S2.5 12 2.5 12Z" />
      <circle cx="12" cy="12" r="2.5" />
    </svg>
  );
}
