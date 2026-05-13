import "./data-display.css";

export type DataSkeletonProps = {
  /** Number of skeleton rows (default 5). */
  rows?: number;
  /** Number of columns (default matches a simple table). */
  columns?: number;
  className?: string;
};

export function DataSkeleton({ rows = 5, columns = 4, className = "" }: DataSkeletonProps) {
  const safeRows = Math.max(1, Math.min(rows, 20));
  const safeCols = Math.max(1, Math.min(columns, 12));

  return (
    <div
      className={`data-skeleton ${className}`.trim()}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label="Loading"
    >
      <div
        className="data-skeleton__grid"
        style={{ gridTemplateColumns: `repeat(${safeCols}, 1fr)` }}
      >
        {Array.from({ length: safeRows * safeCols }).map((_, i) => (
          <div key={i} className="data-skeleton__cell" />
        ))}
      </div>
    </div>
  );
}
