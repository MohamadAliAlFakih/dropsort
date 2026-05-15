import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { BatchDetail as BatchDetailType, BatchState, PredictionOut } from "../api/types";
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
import { PredictionOverlay } from "../components/PredictionOverlay";
import { RefreshButton } from "../components/RefreshButton";
import { StatusBadge } from "../components/data/StatusBadge";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";
import { batchStateLabel, batchStateTone } from "../lib/documentUi";

const POLL_MS = 10_000;

function isBatchPollingState(state: BatchState): boolean {
  return state === "received" || state === "processing";
}

export function BatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [pending, setPending] = useState(true);
  const [detail, setDetail] = useState<BatchDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  const predColumns: DataTableColumn[] = [
    { id: "preview", label: "Preview" },
    { id: "filename", label: "Document" },
    { id: "label", label: "Predicted type" },
    { id: "conf", label: "Confidence", align: "right" },
    { id: "created", label: "Classified" },
  ];

  const load = useCallback(
    async (options?: { silent?: boolean }) => {
      const silent = options?.silent ?? false;
      if (!id) {
        setError("Missing batch id.");
        setPending(false);
        return;
      }
      if (!silent) {
        setPending(true);
        setError(null);
      }
      try {
        const res = await apiFetch(routes.batchDetail(id));
        await assertOk(res);
        const data = (await res.json()) as BatchDetailType;
        setDetail(data);
      } catch (e) {
        if (!silent) {
          setDetail(null);
          setError(getNetworkErrorMessage(e));
        }
      } finally {
        if (!silent) {
          setPending(false);
        }
      }
    },
    [assertOk, id],
  );

  useEffect(() => {
    void load();
  }, [load]);

  const batchState = detail?.batch.state;
  const shouldPoll = Boolean(id && batchState && isBatchPollingState(batchState));

  useEffect(() => {
    if (!shouldPoll) {
      return;
    }
    const handle = window.setInterval(() => {
      void load({ silent: true });
    }, POLL_MS);
    return () => window.clearInterval(handle);
  }, [shouldPoll, load]);

  const batch = detail?.batch;
  const preds: PredictionOut[] = detail?.predictions ?? [];
  const showSkeleton = pending && !batch;

  const headerDescription = shouldPoll
    ? `This batch is still processing. Details refresh about every ${POLL_MS / 1000} seconds until the run completes.`
    : "Summary of this batch and every document the model has classified.";

  return (
    <div className="page">
      <PageHeader
        title="Document batch"
        description={headerDescription}
        actions={
          <>
            <RefreshButton pending={pending || !id} onClick={() => void load()} />
            <Link className="inline-link" to="/batches">
              All batches
            </Link>
          </>
        }
      />

      <ListRefreshingHint show={Boolean(pending && batch)} />
      {showSkeleton ? <DataSkeleton rows={4} columns={3} /> : null}
      <ErrorAlert message={error} />

      {!showSkeleton && batch ? (
        <PageSection title="Overview" description="Status, timing, and how many documents are in this batch.">
          <dl className="batch-meta-dl muted">
            <dt>Batch ID</dt>
            <dd>
              <code>{batch.id}</code>
            </dd>
            <dt>Status</dt>
            <dd>
              <StatusBadge tone={batchStateTone(batch.state)}>{batchStateLabel(batch.state)}</StatusBadge>
            </dd>
            <dt>Source reference</dt>
            <dd>{batch.external_id ?? "Not set"}</dd>
            <dt>Documents in batch</dt>
            <dd>{batch.prediction_count}</dd>
            <dt>Created</dt>
            <dd>{batch.created_at}</dd>
            <dt>Last updated</dt>
            <dd>{batch.updated_at}</dd>
          </dl>
        </PageSection>
      ) : null}

      {!showSkeleton && batch && preds.length === 0 ? (
        <PageSection title="Results">
          <DataEmpty
            title="No classifications yet"
            description="Predictions will show up here as soon as the model finishes scoring each document in this batch."
          />
        </PageSection>
      ) : null}

      {!showSkeleton && preds.length > 0 ? (
        <PageSection
          title="Classified documents"
          description="Review predicted types and model confidence. To correct a low-confidence label, open it from the Review tab."
        >
          <DataTable className="data-table--interactive" columns={predColumns} aria-label="Classified documents">
            {preds.map((p) => (
              <tr key={p.id}>
                <td>
                  <PredictionOverlay
                    predictionId={p.id}
                    filename={p.filename}
                    hasOverlay={Boolean(p.minio_overlay_key)}
                  />
                </td>
                <td className="data-table-cell-strong">{p.filename}</td>
                <td>
                  {p.relabel_label ? (
                    <>
                      {p.relabel_label}{" "}
                      <span className="muted" title={`Originally classified as ${p.label}`}>
                        (corrected)
                      </span>
                    </>
                  ) : (
                    p.label
                  )}
                </td>
                <td className="data-table-cell--numeric">
                  <ConfidenceValue value={p.top1_confidence} />
                </td>
                <td className="data-table-cell-muted">{p.created_at}</td>
              </tr>
            ))}
          </DataTable>
        </PageSection>
      ) : null}
    </div>
  );
}
