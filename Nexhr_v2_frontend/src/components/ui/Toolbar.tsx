import type { ReactNode } from 'react';
import './Toolbar.css';

type ToolbarProps = {
  left?: ReactNode;
  right?: ReactNode;
};

export function Toolbar({ left, right }: ToolbarProps) {
  return (
    <div className="toolbar">
      <div className="toolbar__left">{left}</div>
      <div className="toolbar__right">{right}</div>
    </div>
  );
}
