import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { PredictionOut } from "../api/types";
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
  { id: "batch", label: "Batch" },
  { id: "file", label: "File" },
  { id: "label", label: "Label" },
  { id: "conf", label: "Top-1 conf." },
  { id: "created", label: "Created" },
];

export function PredictionsRecentPage() {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<PredictionOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(routes.predictionsRecent);
      await assertOk(res);
      const data = (await res.json()) as PredictionOut[];
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
      <PageHeader
        title="Recent predictions"
        description="GET /predictions/recent (default limit)."
      />

      <PageSection title="Latest">
        {loading ? <DataSkeleton rows={8} columns={5} /> : null}
        <ErrorAlert message={error} />

        {!loading && rows && rows.length === 0 ? (
          <DataEmpty title="No predictions" description="No recent prediction rows returned." />
        ) : null}

        {!loading && rows && rows.length > 0 ? (
          <DataTable columns={columns} aria-label="Recent predictions">
            {rows.map((p) => (
              <tr key={p.id}>
                <td>
                  <Link className="inline-link" to={`/batches/${p.batch_id}`}>
                    {p.batch_id}
                  </Link>
                </td>
                <td>{p.filename}</td>
                <td>{p.label}</td>
                <td>{p.top1_confidence}</td>
                <td>{p.created_at}</td>
              </tr>
            ))}
          </DataTable>
        ) : null}
      </PageSection>
    </div>
  );
}
