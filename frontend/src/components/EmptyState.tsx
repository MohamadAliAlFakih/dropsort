import type { ReactNode } from "react";

export type EmptyStateProps = {
  title: string;
  description?: string;
  children?: ReactNode;
};

export function EmptyState({ title, description, children }: EmptyStateProps) {
  return (
    <div className="empty-state panel">
      <h2 className="empty-state-title">{title}</h2>
      {description ? <p className="muted">{description}</p> : null}
      {children ? <div className="empty-state-actions">{children}</div> : null}
    </div>
  );
}
