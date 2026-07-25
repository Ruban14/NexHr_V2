import type { ReactNode } from 'react';
import './PageHeader.css';

type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
  breadcrumb?: ReactNode;
};

export function PageHeader({ title, description, actions, breadcrumb }: PageHeaderProps) {
  return (
    <header className="page-header-block">
      <div className="page-header-block__copy">
        {breadcrumb ? <div className="page-header-block__crumb">{breadcrumb}</div> : null}
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {actions ? <div className="page-header-block__actions">{actions}</div> : null}
    </header>
  );
}
