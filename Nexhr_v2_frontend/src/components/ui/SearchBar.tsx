import type { InputHTMLAttributes } from 'react';
import './SearchBar.css';

type SearchBarProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  onValueChange?: (value: string) => void;
};

export function SearchBar({ className = '', onValueChange, onChange, ...props }: SearchBarProps) {
  return (
    <label className={`search-bar ${className}`.trim()}>
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input
        type="search"
        {...props}
        onChange={(event) => {
          onChange?.(event);
          onValueChange?.(event.target.value);
        }}
      />
    </label>
  );
}
