import type { ReactNode } from 'react';
import './Card.css';

export function Card({
  children,
  footer,
  className = '',
}: {
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
}) {
  return (
    <div className={['nex-card', className].filter(Boolean).join(' ')}>
      <div className="nex-card__body">{children}</div>
      {footer ? <div className="nex-card__footer">{footer}</div> : null}
    </div>
  );
}
