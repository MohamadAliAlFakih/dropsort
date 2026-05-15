type LoadingSpinnerProps = {
  label?: string;
};

export function LoadingSpinner({ label = "Loading…" }: LoadingSpinnerProps) {
  return (
    <div className="loading-row" role="status" aria-live="polite">
      <span className="loading-dots" aria-hidden="true">
        <span />
        <span />
        <span />
      </span>
      <p className="muted loading-label">{label}</p>
    </div>
  );
}
