import { Button } from "./Button";

export type PaginationControlsProps = {
  offset: number;
  limit: number;
  rowCount: number;
  limitOptions: readonly number[];
  maxLimit: number;
  pending?: boolean;
  onOffsetChange: (nextOffset: number) => void;
  onLimitChange: (nextLimit: number) => void;
};

/**
 * Offset/limit pager when the API returns a fixed-size window and no total count.
 * "Next" is enabled when the current page is full (`rowCount === limit`).
 */
export function PaginationControls({
  offset,
  limit,
  rowCount,
  limitOptions,
  maxLimit,
  pending,
  onOffsetChange,
  onLimitChange,
}: PaginationControlsProps) {
  const hasPrev = offset > 0;
  const hasNext = rowCount >= limit;
  const start = rowCount === 0 ? 0 : offset + 1;
  const end = offset + rowCount;

  return (
    <div className="pagination-bar" aria-label="Pagination">
      <span aria-live="polite">
        {rowCount === 0 ? "No rows on this page." : `Showing ${start}–${end} of this page (${limit} per page).`}
      </span>
      <span className="pagination-bar__group">
        <label htmlFor="page-limit">Rows per page</label>
        <select
          id="page-limit"
          value={limit}
          disabled={pending}
          onChange={(e) => onLimitChange(Number(e.target.value))}
        >
          {limitOptions
            .filter((n) => n <= maxLimit)
            .map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
        </select>
      </span>
      <span className="pagination-bar__nav">
        <Button
          type="button"
          variant="muted"
          disabled={pending || !hasPrev}
          onClick={() => onOffsetChange(Math.max(0, offset - limit))}
        >
          Previous
        </Button>
        <Button
          type="button"
          variant="muted"
          disabled={pending || !hasNext}
          onClick={() => onOffsetChange(offset + limit)}
        >
          Next
        </Button>
      </span>
    </div>
  );
}
