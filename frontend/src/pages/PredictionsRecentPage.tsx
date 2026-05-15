import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, pathWithQuery } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { PredictionOut, PredictionRelabelIn } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
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
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";

const RELABEL_MAX_TOP1 = 0.7;
const DEFAULT_LIMIT = 50;

const columns: DataTableColumn[] = [
  { id: "preview", label: "Preview" },
  { id: "file", label: "Document" },
  { id: "label", label: "Predicted type" },
  { id: "conf", label: "Confidence", align: "right" },
  { id: "created", label: "Classified" },
  { id: "batch", label: "Batch" },
];

type DetailModalProps = {
  prediction: PredictionOut;
  canRelabel: boolean;
  onClose: () => void;
  onSaved: (updated: PredictionOut) => void;
};

function PredictionDetailModal({ prediction, canRelabel, onClose, onSaved }: DetailModalProps) {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const [overlayUrl, setOverlayUrl] = useState<string | null>(null);
  const [overlayError, setOverlayError] = useState<string | null>(null);

  const [selectedLabel, setSelectedLabel] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const blockedByConfidence = prediction.top1_confidence >= RELABEL_MAX_TOP1;
  const relabelEnabled = canRelabel && !blockedByConfidence;

  useEffect(() => {
    if (!prediction.minio_overlay_key) {
      return;
    }
    let cancelled = false;
    let objectUrl: string | null = null;
    (async () => {
      try {
        const res = await apiFetch(routes.predictionOverlay(prediction.id));
        if (!res.ok) {
          if (!cancelled) setOverlayError("Preview unavailable");
          return;
        }
        const blob = await res.blob();
        objectUrl = URL.createObjectURL(blob);
        if (!cancelled) {
          setOverlayUrl(objectUrl);
        } else {
          URL.revokeObjectURL(objectUrl);
        }
      } catch {
        if (!cancelled) setOverlayError("Preview unavailable");
      }
    })();
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [prediction.id, prediction.minio_overlay_key]);

  useEffect(() => {
    function onKey(ev: KeyboardEvent) {
      if (ev.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function doSave() {
    if (!selectedLabel) return;
    setSaving(true);
    setSaveError(null);
    try {
      const body: PredictionRelabelIn = { label: selectedLabel };
      const res = await apiFetch(routes.predictionDetail(prediction.id), {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      await assertOk(res);
      const updated = (await res.json()) as PredictionOut;
      onSaved(updated);
    } catch (err) {
      setSaveError(getNetworkErrorMessage(err) || "Could not save correction.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">{prediction.filename}</h2>
          <button type="button" className="modal-close" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="modal-body modal-body--split">
          <div className="modal-image-wrap">
            {!prediction.minio_overlay_key ? (
              <div className="modal-image-empty muted">No preview available</div>
            ) : overlayError ? (
              <div className="modal-image-empty muted">{overlayError}</div>
            ) : overlayUrl ? (
              <img className="modal-image" src={overlayUrl} alt={`Preview of ${prediction.filename}`} />
            ) : (
              <div className="modal-image-loading" aria-label="Loading preview" />
            )}
          </div>

          <div className="modal-side">
            <div className="modal-section">
              <div className="modal-section-title">Top 5 predictions</div>
              <ul className="top5-list">
                {prediction.top5.map((t) => {
                  const isCurrent = t.label === prediction.label;
                  const isSelected = t.label === selectedLabel;
                  const itemDisabled = !relabelEnabled || isCurrent || saving;
                  return (
                    <li
                      key={t.label}
                      className={[
                        "top5-item",
                        isCurrent ? "top5-item--current" : "",
                        isSelected ? "top5-item--selected" : "",
                        itemDisabled ? "top5-item--disabled" : "",
                      ]
                        .filter(Boolean)
                        .join(" ")}
                    >
                      <button
                        type="button"
                        className="top5-button"
                        disabled={itemDisabled}
                        onClick={() => setSelectedLabel(t.label)}
                      >
                        <span className="top5-label">{t.label}</span>
                        <span className="top5-score">
                          <ConfidenceValue value={t.score} />
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>

            {canRelabel && blockedByConfidence ? (
              <p className="muted">
                Corrections only allowed when the model's top prediction is below {RELABEL_MAX_TOP1} confidence.
              </p>
            ) : null}

            {!canRelabel ? (
              <p className="muted">Reviewer or admin role is required to change the label.</p>
            ) : null}

            {relabelEnabled && selectedLabel && !confirming ? (
              <div className="modal-actions">
                <Button type="button" variant="muted" onClick={() => setSelectedLabel(null)}>
                  Clear selection
                </Button>
                <Button type="button" onClick={() => setConfirming(true)}>
                  Apply "{selectedLabel}"
                </Button>
              </div>
            ) : null}

            <ErrorAlert message={saveError} />
          </div>
        </div>

        {confirming && selectedLabel ? (
          <div className="modal-confirm">
            <p>
              Change label from <strong>{prediction.label}</strong> to{" "}
              <strong>{selectedLabel}</strong>?
            </p>
            <div className="modal-actions">
              <Button type="button" variant="muted" onClick={() => setConfirming(false)} disabled={saving}>
                Cancel
              </Button>
              <Button type="button" onClick={() => void doSave()} disabled={saving}>
                {saving ? "Saving…" : "Confirm"}
              </Button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export function PredictionsRecentPage() {
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const { me } = useAuth();
  const [pending, setPending] = useState(true);
  const [rows, setRows] = useState<PredictionOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);

  const canRelabel = useMemo(() => me?.role === "admin" || me?.role === "reviewer", [me]);

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
  const opened = useMemo(
    () => (openId ? (rows?.find((r) => r.id === openId) ?? null) : null),
    [openId, rows],
  );

  return (
    <div className="page">
      <PageHeader
        title="Review"
        description="Click a row to open the document, see top-5 predictions, and (for low-confidence results) correct the label."
        actions={<RefreshButton pending={pending} onClick={() => void load()} />}
      />

      <PageSection
        title="Recent classifications"
        description="Newest results first."
      >
        <ListRefreshingHint show={pending && rows !== null && rows.length > 0} />
        {showSkeleton ? <DataSkeleton rows={8} columns={6} /> : null}
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
              <tr
                key={p.id}
                className="data-table-row--clickable"
                onClick={() => setOpenId(p.id)}
              >
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
                <td onClick={(e) => e.stopPropagation()}>
                  <Link className="inline-link" to={`/batches/${p.batch_id}`}>
                    Open batch
                  </Link>
                </td>
              </tr>
            ))}
          </DataTable>
        ) : null}
      </PageSection>

      {opened ? (
        <PredictionDetailModal
          prediction={opened}
          canRelabel={canRelabel}
          onClose={() => setOpenId(null)}
          onSaved={(updated) => {
            setRows((prev) =>
              prev ? prev.map((r) => (r.id === updated.id ? updated : r)) : prev,
            );
            setOpenId(null);
          }}
        />
      ) : null}
    </div>
  );
}
