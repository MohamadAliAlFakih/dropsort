import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, pathWithQuery } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { BatchOut, PredictionOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { ConfidenceValue } from "../components/ConfidenceValue";
import { DataEmpty, DataSkeleton, DataTable, PageSection } from "../components/data";
import type { DataTableColumn } from "../components/data/DataTable";
import { StatusBadge } from "../components/data/StatusBadge";
import { ErrorAlert } from "../components/ErrorAlert";
import { PageHeader } from "../components/PageHeader";
import { batchStateLabel, batchStateTone } from "../lib/documentUi";
import { ROLE_LABELS } from "../lib/roleLabels";

const RECENT_BATCH_LIMIT = 5;
const RECENT_PREDICTION_LIMIT = 5;

const batchColumns: DataTableColumn[] = [
  { id: "id", label: "Batch" },
  { id: "state", label: "Status" },
  { id: "predictions", label: "Documents", align: "right" },
  { id: "updated", label: "Last activity" },
];

const predictionColumns: DataTableColumn[] = [
  { id: "file", label: "Document" },
  { id: "label", label: "Predicted type" },
  { id: "conf", label: "Confidence", align: "right" },
];

function SignedOutHome() {
  return (
    <div className="page page--narrow">
      <PageHeader
        title="Welcome to Dropsort"
        description="Automatic document classification for your team. Sign in to view batches, recent predictions, and team activity."
        actions={
          <Link to="/login">
            <Button type="button">Sign in</Button>
          </Link>
        }
      />
    </div>
  );
}

export function HomePage() {
  const { token, me, meLoading } = useAuth();

  const [batches, setBatches] = useState<BatchOut[] | null>(null);
  const [batchesError, setBatchesError] = useState<string | null>(null);
  const [batchesPending, setBatchesPending] = useState(true);

  const [predictions, setPredictions] = useState<PredictionOut[] | null>(null);
  const [predictionsError, setPredictionsError] = useState<string | null>(null);
  const [predictionsPending, setPredictionsPending] = useState(true);

  const loadBatches = useCallback(async () => {
    setBatchesPending(true);
    setBatchesError(null);
    try {
      const path = pathWithQuery(routes.batches, { offset: 0, limit: RECENT_BATCH_LIMIT });
      const res = await apiFetch(path);
      if (!res.ok) {
        setBatchesError("Could not load recent batches.");
        setBatches(null);
        return;
      }
      const data = (await res.json()) as BatchOut[];
      setBatches(data);
    } catch (e) {
      setBatchesError(getNetworkErrorMessage(e));
      setBatches(null);
    } finally {
      setBatchesPending(false);
    }
  }, []);

  const loadPredictions = useCallback(async () => {
    setPredictionsPending(true);
    setPredictionsError(null);
    try {
      const path = pathWithQuery(routes.predictionsRecent, { limit: RECENT_PREDICTION_LIMIT });
      const res = await apiFetch(path);
      if (!res.ok) {
        setPredictionsError("Could not load recent predictions.");
        setPredictions(null);
        return;
      }
      const data = (await res.json()) as PredictionOut[];
      setPredictions(data);
    } catch (e) {
      setPredictionsError(getNetworkErrorMessage(e));
      setPredictions(null);
    } finally {
      setPredictionsPending(false);
    }
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }
    void loadBatches();
    void loadPredictions();
  }, [token, loadBatches, loadPredictions]);

  if (!token) {
    return <SignedOutHome />;
  }

  const greetingName = me?.email ?? "there";
  const role = me && !meLoading ? ROLE_LABELS[me.role] : null;

  return (
    <div className="page">
      <PageHeader
        title={`Welcome back, ${greetingName}`}
        description={role ? `Signed in as ${role}.` : "Here's what's happening in your workspace."}
        actions={
          <div className="page-header-actions__row">
            <Link to="/batches">
              <Button type="button" variant="muted">
                View all batches
              </Button>
            </Link>
            <Link to="/predictions/recent">
              <Button type="button">View recent predictions</Button>
            </Link>
          </div>
        }
      />

      <PageSection
        title="Recent batches"
        description="The five most recent uploads or ingest jobs."
      >
        {batchesPending && batches === null ? (
          <DataSkeleton rows={3} columns={4} />
        ) : null}
        <ErrorAlert message={batchesError} />
        {batches && batches.length === 0 ? (
          <DataEmpty
            title="No batches yet"
            description="Upload a document or wait for the SFTP ingest to drop a batch."
          />
        ) : null}
        {batches && batches.length > 0 ? (
          <DataTable className="data-table--interactive" columns={batchColumns} aria-label="Recent batches">
            {batches.map((b) => (
              <tr key={b.id}>
                <td>
                  <Link className="inline-link" to={`/batches/${b.id}`}>
                    {b.id}
                  </Link>
                </td>
                <td>
                  <StatusBadge tone={batchStateTone(b.state)}>{batchStateLabel(b.state)}</StatusBadge>
                </td>
                <td className="data-table-cell--numeric">{b.prediction_count}</td>
                <td className="data-table-cell-muted">{b.updated_at}</td>
              </tr>
            ))}
          </DataTable>
        ) : null}
      </PageSection>

      <PageSection
        title="Recent predictions"
        description="The latest documents the classifier scored."
      >
        {predictionsPending && predictions === null ? (
          <DataSkeleton rows={3} columns={3} />
        ) : null}
        <ErrorAlert message={predictionsError} />
        {predictions && predictions.length === 0 ? (
          <DataEmpty
            title="No predictions yet"
            description="Once a batch finishes processing, the latest results will land here."
          />
        ) : null}
        {predictions && predictions.length > 0 ? (
          <DataTable className="data-table--interactive" columns={predictionColumns} aria-label="Recent predictions">
            {predictions.map((p) => (
              <tr key={p.id}>
                <td className="data-table-cell-strong">
                  <Link className="inline-link" to={`/batches/${p.batch_id}`}>
                    {p.filename}
                  </Link>
                </td>
                <td>{p.label}</td>
                <td className="data-table-cell--numeric">
                  <ConfidenceValue value={p.top1_confidence} />
                </td>
              </tr>
            ))}
          </DataTable>
        ) : null}
      </PageSection>
    </div>
  );
}
