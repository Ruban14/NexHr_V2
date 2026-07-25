import './StatusBadge.css';

type StatusBadgeProps = {
  active: boolean;
  activeLabel?: string;
  inactiveLabel?: string;
};

export function StatusBadge({
  active,
  activeLabel = 'Active',
  inactiveLabel = 'Inactive',
}: StatusBadgeProps) {
  return (
    <span className={`status-badge ${active ? 'status-badge--active' : 'status-badge--inactive'}`}>
      <span className="status-badge__dot" aria-hidden />
      {active ? activeLabel : inactiveLabel}
    </span>
  );
}
