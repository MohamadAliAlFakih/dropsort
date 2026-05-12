type LoadingSpinnerProps = {
    label?: string;
  };
  
  export function LoadingSpinner({ label = "Loading…" }: LoadingSpinnerProps) {
    return (
      <p className="muted" role="status" aria-live="polite">
        {label}
      </p>
    );
  }