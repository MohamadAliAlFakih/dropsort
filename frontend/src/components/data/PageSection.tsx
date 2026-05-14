import type { ReactNode } from "react";
import "./data-display.css";

export type PageSectionProps = {
  title?: string;
  description?: ReactNode;
  /** Right-aligned actions (buttons, future filters). */
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function PageSection({
  title,
  description,
  actions,
  children,
  className = "",
}: PageSectionProps) {
  const hasHeader = Boolean(title ?? description ?? actions);

  return (
    <section className={`data-page-section panel ${className}`.trim()}>
      {hasHeader ? (
        <div className="data-page-section__header">
          <div className="data-page-section__titles">
            {title ? <h2 className="data-page-section__title">{title}</h2> : null}
            {description ? (
              <div className="data-page-section__desc muted">{description}</div>
            ) : null}
          </div>
          {actions ? <div className="data-page-section__actions">{actions}</div> : null}
        </div>
      ) : null}
      <div className="data-page-section__body">{children}</div>
    </section>
  );
}
