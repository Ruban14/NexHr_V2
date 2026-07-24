import { useState, type InputHTMLAttributes } from 'react';
import './FormField.css';
import './PasswordInput.css';

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> & {
  label: string;
  error?: string | null;
};

export function PasswordInput({ label, error, id, ...props }: PasswordInputProps) {
  const [visible, setVisible] = useState(false);

  return (
    <label className="form-field" htmlFor={id}>
      <span className="form-field__label">{label}</span>
      <div className="password-input">
        <input
          id={id}
          type={visible ? 'text' : 'password'}
          className={['form-field__input', error ? 'is-invalid' : ''].filter(Boolean).join(' ')}
          {...props}
        />
        <button
          type="button"
          className="password-input__toggle"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Hide password' : 'Show password'}
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      </div>
      {error ? <span className="form-field__error">{error}</span> : null}
    </label>
  );
}
