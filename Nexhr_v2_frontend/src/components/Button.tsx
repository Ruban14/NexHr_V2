import type { ButtonHTMLAttributes, ReactNode } from 'react';
import './Button.css';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'md' | 'lg';
  fullWidth?: boolean;
  loading?: boolean;
  children: ReactNode;
};

export function Button({
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  loading = false,
  disabled,
  children,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      className={[
        'nex-btn',
        `nex-btn--${variant}`,
        `nex-btn--${size}`,
        fullWidth ? 'nex-btn--full' : '',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <span className="nex-btn__spinner" aria-hidden="true" /> : null}
      <span>{children}</span>
    </button>
  );
}
