import type { ReactNode } from "react";
import "./data-display.css";

export type DataTableColumn = {
  id: string;
  label: ReactNode;
  /** Default left */
  align?: "left" | "right";
};

export type DataTableProps = {
  /** Column definitions (stable keys for `th` / `headers` association). */
  columns: DataTableColumn[];
  /** Row cells: typically `<tr key=…>…</tr>` from parent. Omit or pass null when empty. */
  children?: ReactNode;
  /** Accessible name when the table has no visible caption. */
  "aria-label": string;
  className?: string;
};

export function DataTable({
  columns,
  children,
  "aria-label": ariaLabel,
  className = "",
}: DataTableProps) {
  return (
    <div className={`data-table-wrap ${className}`.trim()}>
      <table className="data-table" role="table" aria-label={ariaLabel}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col.id}
                scope="col"
                className={
                  col.align === "right" ? "data-table-th data-table-th--right" : "data-table-th"
                }
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="data-table-body">{children}</tbody>
      </table>
    </div>
  );
}
