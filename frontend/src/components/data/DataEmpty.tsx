import type { ReactNode } from "react";
import "./data-display.css";

export type DataEmptyProps = {
  title: string;
  description?: string;
  children?: ReactNode;
  className?: string;
};

export function DataEmpty({ title, description, children, className = "" }: DataEmptyProps) {
  return (
    <div
      className={`data-empty panel ${className}`.trim()}
      role="status"
      aria-live="polite"
    >
      <h3 className="data-empty__title">{title}</h3>
      {description ? <p className="data-empty__desc muted">{description}</p> : null}
      {children ? <div className="data-empty__actions">{children}</div> : null}
    </div>
  );
}
