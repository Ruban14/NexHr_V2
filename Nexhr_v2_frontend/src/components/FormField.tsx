import type { InputHTMLAttributes } from 'react';
import './FormField.css';

type FormFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string | null;
};

export function FormField({ label, error, id, className = '', ...props }: FormFieldProps) {
  return (
    <label className="form-field" htmlFor={id}>
      <span className="form-field__label">{label}</span>
      <input
        id={id}
        className={['form-field__input', error ? 'is-invalid' : '', className]
          .filter(Boolean)
          .join(' ')}
        {...props}
      />
      {error ? <span className="form-field__error">{error}</span> : null}
    </label>
  );
}
