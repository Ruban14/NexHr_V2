import { useEffect, useState, type FormEvent, type ReactNode } from 'react';
import { Button } from '../Button';
import { Modal } from './Modal';
import './FormModal.css';

export const WEEKDAY_OPTIONS = [
  { value: '1', label: 'Mon' },
  { value: '2', label: 'Tue' },
  { value: '3', label: 'Wed' },
  { value: '4', label: 'Thu' },
  { value: '5', label: 'Fri' },
  { value: '6', label: 'Sat' },
  { value: '7', label: 'Sun' },
] as const;

export type FormFieldConfig = {
  name: string;
  label: string;
  type?: 'text' | 'textarea' | 'time' | 'weekdays' | 'date' | 'number';
  placeholder?: string;
  required?: boolean;
  maxLength?: number;
  min?: number;
  max?: number;
};

type FormModalProps = {
  open: boolean;
  title: string;
  fields: FormFieldConfig[];
  initialValues?: Record<string, string>;
  submitLabel?: string;
  loading?: boolean;
  error?: string | null;
  fieldErrors?: Record<string, string>;
  onSubmit: (values: Record<string, string>) => void | Promise<void>;
  onClose: () => void;
  extra?: ReactNode;
};

function parseWeekdays(value: string): string[] {
  return value
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean);
}

export function FormModal({
  open,
  title,
  fields,
  initialValues = {},
  submitLabel = 'Save',
  loading = false,
  error = null,
  fieldErrors = {},
  onSubmit,
  onClose,
  extra,
}: FormModalProps) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!open) return;
    const next: Record<string, string> = {};
    for (const field of fields) {
      next[field.name] = initialValues[field.name] ?? '';
    }
    setValues(next);
    setLocalErrors({});
  }, [open, fields, initialValues]);

  function reset() {
    const next: Record<string, string> = {};
    for (const field of fields) {
      next[field.name] = initialValues[field.name] ?? '';
    }
    setValues(next);
    setLocalErrors({});
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const nextErrors: Record<string, string> = {};
    for (const field of fields) {
      const value = (values[field.name] || '').trim();
      if (field.required && !value) {
        nextErrors[field.name] =
          field.type === 'weekdays'
            ? 'Select at least one working day.'
            : `${field.label} is required.`;
      }
    }
    setLocalErrors(nextErrors);
    if (Object.keys(nextErrors).length) return;
    await onSubmit(values);
  }

  function toggleWeekday(fieldName: string, day: string) {
    setValues((prev) => {
      const selected = new Set(parseWeekdays(prev[fieldName] || ''));
      if (selected.has(day)) selected.delete(day);
      else selected.add(day);
      return {
        ...prev,
        [fieldName]: Array.from(selected)
          .sort((a, b) => Number(a) - Number(b))
          .join(','),
      };
    });
  }

  return (
    <Modal
      open={open}
      title={title}
      onClose={onClose}
      footer={
        <>
          <Button variant="ghost" type="button" onClick={onClose} disabled={loading}>
            Cancel
          </Button>
          <Button variant="secondary" type="button" onClick={reset} disabled={loading}>
            Reset
          </Button>
          <Button type="submit" form="master-form-modal" loading={loading}>
            {submitLabel}
          </Button>
        </>
      }
    >
      <form id="master-form-modal" className="form-modal" onSubmit={handleSubmit}>
        {error ? <div className="auth-alert auth-alert--error">{error}</div> : null}
        {fields.map((field) => {
          const message = localErrors[field.name] || fieldErrors[field.name];
          if (field.type === 'weekdays') {
            const selected = new Set(parseWeekdays(values[field.name] || ''));
            return (
              <div key={field.name} className="form-modal__field">
                <span>
                  {field.label}
                  {field.required ? ' *' : ''}
                </span>
                <div className="form-modal__weekdays">
                  {WEEKDAY_OPTIONS.map((day) => {
                    const active = selected.has(day.value);
                    return (
                      <button
                        key={day.value}
                        type="button"
                        className={`form-modal__weekday${active ? ' is-active' : ''}`}
                        aria-pressed={active}
                        onClick={() => toggleWeekday(field.name, day.value)}
                      >
                        {day.label}
                      </button>
                    );
                  })}
                </div>
                {message ? <em>{message}</em> : null}
              </div>
            );
          }

          return (
            <label key={field.name} className="form-modal__field">
              <span>
                {field.label}
                {field.required ? ' *' : ''}
              </span>
              {field.type === 'textarea' ? (
                <textarea
                  value={values[field.name] || ''}
                  placeholder={field.placeholder}
                  maxLength={field.maxLength}
                  rows={3}
                  onChange={(event) =>
                    setValues((prev) => ({ ...prev, [field.name]: event.target.value }))
                  }
                />
              ) : (
                <input
                  type={
                    field.type === 'time' || field.type === 'date' || field.type === 'number'
                      ? field.type
                      : 'text'
                  }
                  value={values[field.name] || ''}
                  placeholder={field.placeholder}
                  maxLength={field.maxLength}
                  min={field.min}
                  max={field.max}
                  onChange={(event) =>
                    setValues((prev) => ({ ...prev, [field.name]: event.target.value }))
                  }
                />
              )}
              {message ? <em>{message}</em> : null}
            </label>
          );
        })}
        {extra}
      </form>
    </Modal>
  );
}
