import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, pathWithQuery } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { PredictionOut } from "../api/types";
import { ConfidenceValue } from "../components/ConfidenceValue";
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
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";

const columns: DataTableColumn[] = [
  { id: "batch", label: "Batch" },
  { id: "file", label: "Document" },
  { id: "label", label: "Predicted type" },
  { id: "conf", label: "Confidence", align: "right" },
  { id: "created", label: "Classified" },
];

const DEFAULT_LIMIT = 50;

export function PredictionsRecentPage() {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [pending, setPending] = useState(true);
  const [rows, setRows] = useState<PredictionOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      const path = pathWithQuery(routes.predictionsRecent, { limit: DEFAULT_LIMIT });
      const res = await apiFetch(path);
      await assertOk(res);
      const data = (await res.json()) as PredictionOut[];
      setRows(data);
    } catch (e) {
      setRows(null);
      setError(getNetworkErrorMessage(e));
    } finally {
      setPending(false);
    }
  }, [assertOk]);

  useEffect(() => {
    void load();
  }, [load]);

  const showSkeleton = pending && rows === null;

  return (
    <div className="page">
      <PageHeader
        title="Recent classifications"
        description="The latest documents the model has scored. Open a batch from any row for full context."
        actions={<RefreshButton pending={pending} onClick={() => void load()} />}
      />

      <PageSection
        title="Activity"
        description="Newest results first. Each entry links to its processing batch."
      >
        <ListRefreshingHint show={pending && rows !== null && rows.length > 0} />
        {showSkeleton ? <DataSkeleton rows={8} columns={5} /> : null}
        <ErrorAlert message={error} />

        {!showSkeleton && rows && rows.length === 0 ? (
          <DataEmpty
            title="No recent activity"
            description="Once the pipeline classifies documents, the most recent results will appear here."
          />
        ) : null}

        {!showSkeleton && rows && rows.length > 0 ? (
          <DataTable className="data-table--interactive" columns={columns} aria-label="Recent classifications">
            {rows.map((p) => (
              <tr key={p.id}>
                <td>
                  <Link className="inline-link" to={`/batches/${p.batch_id}`}>
                    {p.batch_id}
                  </Link>
                </td>
                <td className="data-table-cell-strong">{p.filename}</td>
                <td>{p.label}</td>
                <td className="data-table-cell--numeric">
                  <ConfidenceValue value={p.top1_confidence} />
                </td>
                <td className="data-table-cell-muted">{p.created_at}</td>
              </tr>
            ))}
          </DataTable>
        ) : null}
      </PageSection>
    </div>
  );
}
