import { useEffect, type ReactNode } from 'react';
import './Modal.css';

type ModalProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  size?: 'md' | 'lg';
};

export function Modal({ open, title, onClose, children, footer, size = 'md' }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', onKeyDown);
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previous;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="modal-root" role="presentation">
      <button type="button" className="modal-backdrop" aria-label="Close dialog" onClick={onClose} />
      <div
        className={`modal-panel modal-panel--${size}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <header className="modal-panel__header">
          <h2 id="modal-title">{title}</h2>
          <button type="button" className="modal-panel__close" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </header>
        <div className="modal-panel__body">{children}</div>
        {footer ? <footer className="modal-panel__footer">{footer}</footer> : null}
      </div>
    </div>
  );
}
