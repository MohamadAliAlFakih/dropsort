/**
 * Shown when a list already has rows but a new fetch is in progress (non-skeleton refresh).
 */
export function ListRefreshingHint({ show }: { show: boolean }) {
  if (!show) {
    return null;
  }
  return (
    <p className="list-refreshing-hint" role="status" aria-live="polite">
      Refreshing results…
    </p>
  );
}
