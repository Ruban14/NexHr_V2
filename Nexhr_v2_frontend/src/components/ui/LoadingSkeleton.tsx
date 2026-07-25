import './LoadingSkeleton.css';

type LoadingSkeletonProps = {
  rows?: number;
};

export function LoadingSkeleton({ rows = 5 }: LoadingSkeletonProps) {
  return (
    <div className="loading-skeleton" aria-busy="true" aria-label="Loading">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="loading-skeleton__row">
          <span className="loading-skeleton__bar loading-skeleton__bar--lg" />
          <span className="loading-skeleton__bar" />
          <span className="loading-skeleton__bar loading-skeleton__bar--sm" />
        </div>
      ))}
    </div>
  );
}
