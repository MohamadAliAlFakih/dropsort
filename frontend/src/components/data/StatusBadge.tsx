import type { ReactNode } from "react";
import "./data-display.css";

export type StatusBadgeTone = "neutral" | "info" | "success" | "warning" | "danger";

export type StatusBadgeProps = {
  tone?: StatusBadgeTone;
  children: ReactNode;
  className?: string;
};

export function StatusBadge({ tone = "neutral", children, className = "" }: StatusBadgeProps) {
  return (
    <span className={`data-badge data-badge--${tone} ${className}`.trim()}>{children}</span>
  );
}
