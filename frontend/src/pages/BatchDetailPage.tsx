import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { BatchDetail as BatchDetailType, PredictionOut } from "../api/types";
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

const predColumns: DataTableColumn[] = [
  { id: "filename", label: "File" },
  { id: "label", label: "Label" },
  { id: "conf", label: "Top-1 conf." },
  { id: "created", label: "Created" },
];

export function BatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<BatchDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) {
      setError("Missing batch id.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await apiFetch(routes.batchDetail(id));
      await assertOk(res);
      const data = (await res.json()) as BatchDetailType;
      setDetail(data);
    } catch (e) {
      setDetail(null);
      setError(getNetworkErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [assertOk, id]);

  useEffect(() => {
    void load();
  }, [load]);

  const batch = detail?.batch;
  const preds: PredictionOut[] = detail?.predictions ?? [];

  return (
    <div className="page">
      <PageHeader
        title="Batch detail"
        description="GET /batches/{batch_id}"
        actions={
          <Link className="inline-link" to="/batches">
            Back to batches
          </Link>
        }
      />

      {loading ? <DataSkeleton rows={4} columns={3} /> : null}
      <ErrorAlert message={error} />

      {!loading && batch ? (
        <PageSection title="Batch">
          <dl
            className="muted"
            style={{
              display: "grid",
              gridTemplateColumns: "auto 1fr",
              gap: "0.5rem 1rem",
            }}
          >
            <dt>Id</dt>
            <dd style={{ margin: 0 }}>
              <code>{batch.id}</code>
            </dd>
            <dt>State</dt>
            <dd style={{ margin: 0 }}>
              <StatusBadge tone="neutral">{batch.state}</StatusBadge>
            </dd>
            <dt>External id</dt>
            <dd style={{ margin: 0 }}>{batch.external_id ?? "—"}</dd>
            <dt>Predictions</dt>
            <dd style={{ margin: 0 }}>{batch.prediction_count}</dd>
            <dt>Created</dt>
            <dd style={{ margin: 0 }}>{batch.created_at}</dd>
            <dt>Updated</dt>
            <dd style={{ margin: 0 }}>{batch.updated_at}</dd>
          </dl>
        </PageSection>
      ) : null}

      {!loading && batch && preds.length === 0 ? (
        <PageSection title="Predictions">
          <DataEmpty title="No predictions" description="This batch has no prediction rows yet." />
        </PageSection>
      ) : null}

      {!loading && preds.length > 0 ? (
        <PageSection title="Predictions">
          <DataTable columns={predColumns} aria-label="Predictions for batch">
            {preds.map((p) => (
              <tr key={p.id}>
                <td>{p.filename}</td>
                <td>{p.label}</td>
                <td>{p.top1_confidence}</td>
                <td>{p.created_at}</td>
              </tr>
            ))}
          </DataTable>
        </PageSection>
      ) : null}
    </div>
  );
}
