import type { ReactNode } from "react";
import "./data-display.css";

export type DataToolbarProps = {
  start?: ReactNode;
  end?: ReactNode;
  className?: string;
};

export function DataToolbar({ start, end, className = "" }: DataToolbarProps) {
  if (!start && !end) {
    return null;
  }

  return (
    <div className={`data-toolbar ${className}`.trim()} role="toolbar" aria-label="Table tools">
      <div className="data-toolbar__start">{start}</div>
      <div className="data-toolbar__end">{end}</div>
    </div>
  );
}
