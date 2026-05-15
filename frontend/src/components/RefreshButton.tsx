import { Button } from "./Button";

export type RefreshButtonProps = {
  pending: boolean;
  onClick: () => void;
  className?: string;
};

/**
 * Shared toolbar refresh control: muted style, disabled + label while a request is in flight.
 */
export function RefreshButton({ pending, onClick, className = "" }: RefreshButtonProps) {
  return (
    <Button
      type="button"
      variant="muted"
      className={className}
      disabled={pending}
      aria-busy={pending}
      onClick={onClick}
    >
      {pending ? "Refreshing…" : "Refresh"}
    </Button>
  );
}
