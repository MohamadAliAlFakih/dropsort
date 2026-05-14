import type { FormEvent } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { apiFetch } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type {
  BatchDetail as BatchDetailType,
  BatchState,
  PredictionOut,
  PredictionRelabelIn,
} from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ConfidenceValue } from "../components/ConfidenceValue";
import {
  DataEmpty,
  DataSkeleton,
  DataTable,
  PageSection,
} from "../components/data";
import type { DataTableColumn } from "../components/data/DataTable";
import { ErrorAlert } from "../components/ErrorAlert";
import { Button } from "../components/Button";
import { ListRefreshingHint } from "../components/ListRefreshingHint";
import { PageHeader } from "../components/PageHeader";
import { RefreshButton } from "../components/RefreshButton";
import { StatusBadge } from "../components/data/StatusBadge";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";
import { batchStateLabel, batchStateTone } from "../lib/documentUi";

const POLL_MS = 10_000;

/** Matches `RELABEL_CONFIDENCE_THRESHOLD` in `app/services/prediction_service.py` (AUTH-05). */
const RELABEL_MAX_TOP1 = 0.7;

/** DB `relabel_label` column length (`app/db/models.py`). */
const RELABEL_LABEL_MAX_LEN = 64;

function isBatchPollingState(state: BatchState): boolean {
  return state === "received" || state === "processing";
}

function relabelSuggestionLabels(p: PredictionOut): string[] {
  const uniq = new Set<string>();
  uniq.add(p.label);
  for (const t of p.top5) {
    uniq.add(t.label);
  }
  return [...uniq];
}

type PredictionRelabelCellProps = {
  prediction: PredictionOut;
  assertOk: (res: Response) => Promise<Response>;
  patchingId: string | null;
  setPatchingId: (id: string | null) => void;
  onRelabeled: () => Promise<void>;
};

function PredictionRelabelCell({
  prediction: p,
  assertOk,
  patchingId,
  setPatchingId,
  onRelabeled,
}: PredictionRelabelCellProps) {
  const [draft, setDraft] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const blockedByConfidence = p.top1_confidence >= RELABEL_MAX_TOP1;
  const isThisPatching = patchingId === p.id;
  const isOtherPatching = patchingId !== null && patchingId !== p.id;
  const disabled = blockedByConfidence || isOtherPatching || isThisPatching;

  const suggestions = useMemo(() => relabelSuggestionLabels(p), [p]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const label = draft.trim();
    if (!label) {
      setLocalError("Enter the corrected document type.");
      return;
    }
    setLocalError(null);
    setPatchingId(p.id);
    try {
      const body: PredictionRelabelIn = { label };
      const res = await apiFetch(routes.predictionDetail(p.id), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await assertOk(res);
      await onRelabeled();
      setDraft("");
    } catch (err) {
      const msg = getNetworkErrorMessage(err);
      setLocalError(msg || "Could not save correction.");
    } finally {
      setPatchingId(null);
    }
  }

  const listId = `relabel-hints-${p.id}`;

  return (
    <form className="prediction-correction" onSubmit={(ev) => void onSubmit(ev)}>
      {blockedByConfidence ? (
        <p className="prediction-correction__blocked muted">
          Corrections are available when the model is uncertain (confidence on the top prediction below{" "}
          {RELABEL_MAX_TOP1}).
        </p>
      ) : (
        <>
          <datalist id={listId}>
            {suggestions.map((lab) => (
              <option key={lab} value={lab} />
            ))}
          </datalist>
          <div className="prediction-correction__row">
            <input
              type="text"
              className="input-inline"
              value={draft}
              onChange={(ev) => setDraft(ev.target.value)}
              list={listId}
              maxLength={RELABEL_LABEL_MAX_LEN}
              disabled={disabled}
              placeholder="Corrected type"
              aria-label={`Correct document type for ${p.filename}`}
            />
            <Button type="submit" variant="muted" disabled={disabled}>
              {isThisPatching ? "Saving…" : "Save"}
            </Button>
          </div>
        </>
      )}
      {localError ? (
        <span className="prediction-correction__err" role="alert">
          {localError}
        </span>
      ) : null}
    </form>
  );
}

export function BatchDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { me, meLoading } = useAuth();
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [pending, setPending] = useState(true);
  const [detail, setDetail] = useState<BatchDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [patchingPredictionId, setPatchingPredictionId] = useState<string | null>(null);

  const canRelabel = Boolean(me && !meLoading && me.role === "reviewer");

  const predColumns = useMemo<DataTableColumn[]>(() => {
    const base: DataTableColumn[] = [
      { id: "filename", label: "Document" },
      { id: "label", label: "Predicted type" },
      { id: "conf", label: "Confidence", align: "right" },
      { id: "created", label: "Classified" },
    ];
    if (canRelabel) {
      return [...base, { id: "relabel", label: "Correction" }];
    }
    return base;
  }, [canRelabel]);

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

  const handleRelabeled = useCallback(async () => {
    await load({ silent: true });
  }, [load]);

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
            <dd>{batch.external_id ?? "—"}</dd>
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
          description={
            canRelabel
              ? "Review predicted types and confidence. When the model is uncertain, reviewers can submit a correction."
              : "Review predicted types and model confidence for each file."
          }
        >
          <DataTable className="data-table--interactive" columns={predColumns} aria-label="Classified documents">
            {preds.map((p) => (
              <tr key={p.id}>
                <td className="data-table-cell-strong">{p.filename}</td>
                <td>{p.label}</td>
                <td className="data-table-cell--numeric">
                  <ConfidenceValue value={p.top1_confidence} />
                </td>
                <td className="data-table-cell-muted">{p.created_at}</td>
                {canRelabel ? (
                  <td>
                    <PredictionRelabelCell
                      prediction={p}
                      assertOk={assertOk}
                      patchingId={patchingPredictionId}
                      setPatchingId={setPatchingPredictionId}
                      onRelabeled={handleRelabeled}
                    />
                  </td>
                ) : null}
              </tr>
            ))}
          </DataTable>
        </PageSection>
      ) : null}
    </div>
  );
}
