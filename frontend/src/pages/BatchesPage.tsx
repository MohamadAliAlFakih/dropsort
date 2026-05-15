import { useCallback, useEffect, useRef, useState, type ChangeEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { apiFetch, pathWithQuery } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { routes } from "../api/routes";
import type { BatchOut, BatchUploadAccepted } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
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
import { StatusBadge } from "../components/data/StatusBadge";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";
import { batchStateLabel, batchStateTone } from "../lib/documentUi";

const columns: DataTableColumn[] = [
  { id: "id", label: "Batch" },
  { id: "state", label: "Status" },
  { id: "predictions", label: "Documents", align: "right" },
  { id: "created", label: "Last activity" },
];

const LIMIT_OPTIONS = [10, 25, 50] as const;
const MAX_LIMIT = 100;
const DEFAULT_LIMIT = 25;

export function BatchesPage() {
  const navigate = useNavigate();
  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: true });
  const { me, meLoading } = useAuth();
  const [offset, setOffset] = useState(0);
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [pending, setPending] = useState(true);
  const [rows, setRows] = useState<BatchOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadPending, setUploadPending] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const canUpload = Boolean(me && !meLoading && (me.role === "reviewer" || me.role === "admin"));

  const load = useCallback(async () => {
    setPending(true);
    setError(null);
    try {
      const path = pathWithQuery(routes.batches, { offset, limit });
      const res = await apiFetch(path);
      await assertOk(res);
      const data = (await res.json()) as BatchOut[];
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

  async function onTiffSelected(ev: ChangeEvent<HTMLInputElement>) {
    const input = ev.currentTarget;
    const files = input.files ? Array.from(input.files) : [];
    input.value = "";
    if (files.length === 0) {
      return;
    }
    setUploadError(null);
    setUploadPending(true);
    let lastBatchId: string | null = null;
    const failures: string[] = [];
    try {
      for (const file of files) {
        try {
          const fd = new FormData();
          fd.append("file", file, file.name);
          const res = await apiFetch(routes.batchesUpload, { method: "POST", body: fd });
          await assertOk(res);
          const data = (await res.json()) as BatchUploadAccepted;
          lastBatchId = data.batch.id;
        } catch (perFile) {
          failures.push(`${file.name}: ${getNetworkErrorMessage(perFile) || "upload failed"}`);
        }
      }
      await load();
      if (failures.length > 0) {
        setUploadError(
          `${files.length - failures.length} of ${files.length} uploaded. Failed: ${failures.join("; ")}`,
        );
      }
      if (lastBatchId && failures.length === 0) {
        navigate(`/batches/${lastBatchId}`);
      }
    } finally {
      setUploadPending(false);
    }
  }

  const showSkeleton = pending && rows === null;

  return (
    <div className="page">
      <PageHeader
        title="Processing dashboard"
        description="Track document batches as they move through classification. Open a batch to review individual results."
        actions={<RefreshButton pending={pending} onClick={() => void load()} />}
      />

      {canUpload ? (
        <PageSection
          title="Scan simulator"
          description="Drop a document to send it through the classifier."
        >
          <div className="panel batch-upload-bar">
            <p className="muted batch-upload-bar__hint">
              Pick one or more documents. Each becomes its own batch.
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".tif,.tiff,image/tiff"
              multiple
              disabled={uploadPending}
              onChange={(ev) => void onTiffSelected(ev)}
              hidden
            />
            <Button
              type="button"
              disabled={uploadPending}
              onClick={() => fileInputRef.current?.click()}
            >
              {uploadPending ? "Uploading…" : "Choose documents"}
            </Button>
          </div>
          <ErrorAlert message={uploadError} />
        </PageSection>
      ) : null}

      <PageSection
        title="Batches"
        description="Each row is one upload or job. Status shows where that work sits in the pipeline."
      >
        <ListRefreshingHint show={pending && rows !== null && rows.length > 0} />
        {showSkeleton ? <DataSkeleton rows={6} columns={4} /> : null}
        <ErrorAlert message={error} />

        {!showSkeleton && rows && rows.length === 0 ? (
          <DataEmpty
            title="No batches yet"
            description="When new documents are ingested and classified, they will appear here. If you expect traffic already, check your ingestion pipeline and try refreshing."
          />
        ) : null}

        {!showSkeleton && rows && rows.length > 0 ? (
          <DataTable className="data-table--interactive" columns={columns} aria-label="Document batches">
            {rows.map((b) => (
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
