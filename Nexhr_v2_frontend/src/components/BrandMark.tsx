import './BrandMark.css';

type BrandMarkProps = {
  size?: 'sm' | 'lg';
  tone?: 'default' | 'inverse';
  showWordmark?: boolean;
};

export function BrandMark({
  size = 'sm',
  tone = 'default',
  showWordmark = true,
}: BrandMarkProps) {
  return (
    <div className={`brand-mark brand-mark--${size} brand-mark--${tone}`}>
      <span className="brand-mark__badge" aria-hidden="true">
        N
      </span>
      {showWordmark ? (
        <div className="brand-mark__text">
          <strong>NexHr</strong>
          <span>Enterprise HR Platform</span>
        </div>
      ) : null}
    </div>
  );
}
