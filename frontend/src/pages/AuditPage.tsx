import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../api/client";
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
import { PageHeader } from "../components/PageHeader";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";

const columns: DataTableColumn[] = [
  { id: "time", label: "Time" },
  { id: "action", label: "Action" },
  { id: "target", label: "Target" },
  { id: "actor", label: "Actor" },
];

export function AuditPage() {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<AuditEntryOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(routes.audit);
      await assertOk(res);
      const data = (await res.json()) as AuditEntryOut[];
      setRows(data);
    } catch (e) {
      setRows(null);
      setError(getNetworkErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [assertOk]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="page">
      <PageHeader title="Audit log" description="GET /audit (default offset and limit)." />

      <PageSection title="Entries">
        {loading ? <DataSkeleton rows={8} columns={4} /> : null}
        <ErrorAlert message={error} />

        {!loading && rows && rows.length === 0 ? (
          <DataEmpty title="No audit entries" description="The audit log is empty for this request." />
        ) : null}

        {!loading && rows && rows.length > 0 ? (
          <DataTable columns={columns} aria-label="Audit log entries">
            {rows.map((a) => (
              <tr key={a.id}>
                <td>{a.created_at}</td>
                <td>{a.action}</td>
                <td>
                  {a.target_type} / <code>{a.target_id}</code>
                </td>
                <td>
                  <code>{a.actor_id}</code>
                </td>
              </tr>
            ))}
          </DataTable>
        ) : null}
      </PageSection>
    </div>
  );
}
