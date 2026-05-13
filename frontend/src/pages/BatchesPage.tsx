import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { BatchOut } from "../api/types";
import {
  DataEmpty,
  DataSkeleton,
  DataTable,
  PageSection,
} from "../components/data";
import type { DataTableColumn } from "../components/data/DataTable";
import { ErrorAlert } from "../components/ErrorAlert";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/data/StatusBadge";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";

const columns: DataTableColumn[] = [
  { id: "id", label: "Id" },
  { id: "state", label: "State" },
  { id: "predictions", label: "Predictions" },
  { id: "created", label: "Created" },
];

export function BatchesPage() {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<BatchOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(routes.batches);
      await assertOk(res);
      const data = (await res.json()) as BatchOut[];
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
      <PageHeader title="Batches" description="GET /batches (default offset and limit)." />

      <PageSection title="All batches">
        {loading ? <DataSkeleton rows={6} columns={4} /> : null}
        <ErrorAlert message={error} />

        {!loading && rows && rows.length === 0 ? (
          <DataEmpty title="No batches" description="The list is empty." />
        ) : null}

        {!loading && rows && rows.length > 0 ? (
          <DataTable columns={columns} aria-label="Batches">
            {rows.map((b) => (
              <tr key={b.id}>
                <td>
                  <Link className="inline-link" to={`/batches/${b.id}`}>
                    {b.id}
                  </Link>
                </td>
                <td>
                  <StatusBadge tone="neutral">{b.state}</StatusBadge>
                </td>
                <td>{b.prediction_count}</td>
                <td>{b.created_at}</td>
              </tr>
            ))}
          </DataTable>
        ) : null}
      </PageSection>
    </div>
  );
}
