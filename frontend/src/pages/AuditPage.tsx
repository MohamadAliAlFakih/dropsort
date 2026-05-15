import { useCallback, useEffect, useState } from "react";
import { apiFetch, pathWithQuery } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { AuditEntryOut } from "../api/types";
import {
  DataEmpty,
  DataSkeleton,
  DataTable,
  PageSection,
} from "../components/data";
import type { DataTableColumn } from "../components/data/DataTable";
import { ErrorAlert } from "../components/ErrorAlert";
import { ListRefreshingHint } from "../components/ListRefreshingHint";
import { PageHeader } from "../components/PageHeader";
import { RefreshButton } from "../components/RefreshButton";
import { PaginationControls } from "../components/PaginationControls";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";
import { shortId } from "../lib/formatId";

const columns: DataTableColumn[] = [
  { id: "time", label: "When" },
  { id: "action", label: "Event" },
  { id: "actor", label: "Actor" },
  { id: "target", label: "Subject" },
];

const LIMIT_OPTIONS = [10, 25, 50, 100] as const;
const MAX_LIMIT = 200;
const DEFAULT_LIMIT = 25;

function formatAuditWhen(iso: string): { line1: string; line2: string } {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) {
    return { line1: iso, line2: "" };
  }
  return {
    line1: d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" }),
    line2: iso,
  };
}

function humanizeAction(action: string): string {
  return action.replace(/_/g, " ");
}

export function AuditPage() {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [pending, setPending] = useState(true);
  const [rows, setRows] = useState<AuditEntryOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      const path = pathWithQuery(routes.audit, { offset, limit });
      const res = await apiFetch(path);
      await assertOk(res);
      const data = (await res.json()) as AuditEntryOut[];
      setRows(data);
    } catch (e) {
      setRows(null);
      setError(getNetworkErrorMessage(e));
    } finally {
      setPending(false);
    }
  }, [assertOk, offset, limit]);

  useEffect(() => {
    void load();
  }, [load]);

  const showSkeleton = pending && rows === null;

  return (
    <div className="page">
      <PageHeader
        title="Activity history"
        description="Review security and workflow events across accounts and documents. Useful for compliance reviews and operational follow-up."
        actions={<RefreshButton pending={pending} onClick={() => void load()} />}
      />

      <PageSection
        title="Audit trail"
        description="Each row is an immutable record of who did what, and on which resource. People and documents are shown in readable form when the data is available."
      >
        <ListRefreshingHint show={pending && rows !== null && rows.length > 0} />
        {showSkeleton ? <DataSkeleton rows={8} columns={4} /> : null}
        <ErrorAlert message={error} />

        {!showSkeleton && rows && rows.length === 0 ? (
          <DataEmpty
            title="No events in this view"
            description="Try another page of results or adjust how many rows you show per page."
          />
        ) : null}

        {!showSkeleton && rows && rows.length > 0 ? (
          <DataTable
            className="data-table--interactive audit-table"
            columns={columns}
            aria-label="Audit events"
          >
            {rows.map((a) => {
              const when = formatAuditWhen(a.created_at);
              const actorPrimary = a.actor_email?.trim() || shortId(a.actor_id);
              const subjectPrimary = (a.target_label && a.target_label.trim()) || shortId(a.target_id);
              return (
                <tr key={a.id}>
                  <td className="audit-cell-time">
                    <div className="audit-time-stack">
                      <span className="audit-time-primary">{when.line1}</span>
                      {when.line2 ? <span className="audit-time-secondary">{when.line2}</span> : null}
                    </div>
                  </td>
                  <td className="audit-cell-action">
                    <span className="audit-action">{humanizeAction(a.action)}</span>
                    <span className="audit-action-code muted">{a.action}</span>
                  </td>
                  <td className="audit-cell-identity">
                    <div className="audit-identity-primary">{actorPrimary}</div>
                    <div className="audit-identity-meta muted">
                      <span className="audit-identity-id" title={a.actor_id}>
                        {shortId(a.actor_id)}
                      </span>
                    </div>
                  </td>
                  <td className="audit-cell-subject">
                    <div className="audit-target-type muted">{a.target_type}</div>
                    <div className="audit-identity-primary">{subjectPrimary}</div>
                    <div className="audit-identity-meta muted">
                      <span title={a.target_id}>{shortId(a.target_id)}</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </DataTable>
        ) : null}

        {rows ? (
          <PaginationControls
            offset={offset}
            limit={limit}
            rowCount={rows.length}
            limitOptions={LIMIT_OPTIONS}
            maxLimit={MAX_LIMIT}
            pending={pending}
            onOffsetChange={setOffset}
            onLimitChange={(next) => {
              setLimit(next);
              setOffset(0);
            }}
          />
        ) : null}
      </PageSection>
    </div>
  );
}
