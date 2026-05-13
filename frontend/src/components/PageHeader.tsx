import type { ReactNode } from "react";

export type PageHeaderProps = {
  title: string;
  description?: string;
  actions?: ReactNode;
};

/**
 * Page-level heading block (not the site chrome <header> in Layout).
 */
export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-header-row">
        <h1 className="page-title">{title}</h1>
        {actions ? <div className="page-header-actions">{actions}</div> : null}
      </div>
      {description ? (
        <p className="muted page-header-desc">{description}</p>
      ) : null}
    </div>
  );
}