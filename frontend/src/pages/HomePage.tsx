import { useState } from "react";
import { apiFetch } from "../api/client";
import { routes } from "../api/routes";
import { ApiHttpError, getNetworkErrorMessage } from "../api/httpErrors";
import { Button } from "../components/Button";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import {
  healthServiceTitle,
  isHealthPayload,
  orderedHealthDepKeys,
  type HealthDepCheck,
  type HealthPayload,
} from "../lib/healthPayload";

const SLOW_OK_LATENCY_MS = 400;

function depStatusTone(dep: HealthDepCheck): "success" | "warning" | "danger" {
  if (dep.status !== "ok") {
    return "danger";
  }
  const ms = dep.latency_ms;
  if (typeof ms === "number" && Number.isFinite(ms) && ms >= SLOW_OK_LATENCY_MS) {
    return "warning";
  }
  return "success";
}

function HealthStatusDot({ tone }: { tone: "success" | "warning" | "danger" }) {
  return <span className={`health-dot health-dot--${tone}`} aria-hidden="true" />;
}

function ServiceHealthCard({
  depKey,
  title,
  dep,
}: {
  depKey: string;
  title: string;
  dep: HealthDepCheck;
}) {
  const tone = depStatusTone(dep);
  const operational = dep.status === "ok";
  const latencySlow = operational && tone === "warning";
  const latency =
    typeof dep.latency_ms === "number" && Number.isFinite(dep.latency_ms) ? (
      <span className={`health-latency-chip${latencySlow ? " health-latency-chip--slow" : ""}`}>
        {dep.latency_ms} ms
        {latencySlow ? <span className="health-latency-chip__hint"> elevated</span> : null}
      </span>
    ) : null;
  const extra =
    depKey === "casbin_policy" && typeof dep.policy_count === "number" ? (
      <p className="health-card__meta muted">{dep.policy_count} access rules loaded</p>
    ) : null;
  const err = dep.error ? (
    <p className="health-card__err muted" role="status">
      {dep.error}
    </p>
  ) : null;

  return (
    <article className="health-card">
      <div className="health-card__head">
        <HealthStatusDot tone={tone} />
        <h3 className="health-card__title">{title}</h3>
        <span className={`health-card__badge health-card__badge--${tone}`}>
          {operational ? "Operational" : "Unavailable"}
        </span>
      </div>
      <div className="health-card__body">
        {latency}
        {extra}
        {err}
      </div>
    </article>
  );
}

export function HomePage() {
  const [loading, setLoading] = useState(false);
  const [payload, setPayload] = useState<HealthPayload | null>(null);
  const [httpStatus, setHttpStatus] = useState<number | null>(null);
  const [rawBody, setRawBody] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function checkHealth() {
    setLoading(true);
    setError(null);
    setPayload(null);
    setRawBody(null);
    setHttpStatus(null);
    try {
      const res = await apiFetch(routes.health, { auth: false });
      const text = await res.text();
      setRawBody(text);
      let parsed: unknown;
      try {
        parsed = text ? JSON.parse(text) : null;
      } catch {
        setError("Could not read health response.");
        return;
      }
      if (!isHealthPayload(parsed)) {
        setError(
          res.ok
            ? "Health response was not in the expected format."
            : getNetworkErrorMessage(new ApiHttpError(res.status, text)),
        );
        return;
      }
      setPayload(parsed);
      setHttpStatus(res.status);
      setLastChecked(new Date());
      if (!res.ok && res.status !== 503) {
        setError(getNetworkErrorMessage(new ApiHttpError(res.status, text)));
      }
    } catch (e) {
      setError(getNetworkErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  const overallOk = Boolean(payload?.ok === true && httpStatus === 200);

  return (
    <div className="page">
      <PageHeader
        title="Platform health"
        description="On-demand checks against the live environment—useful before handoffs or when validating an incident."
        actions={
          <Button type="button" onClick={() => void checkHealth()} disabled={loading}>
            {loading ? "Checking…" : "Run health check"}
          </Button>
        }
      />

      {loading ? <LoadingSpinner label="Running dependency checks…" /> : null}
      <ErrorAlert message={error} />

      {lastChecked ? (
        <p className="health-last-checked muted" role="status">
          Last checked: {lastChecked.toLocaleString()}
        </p>
      ) : null}

      {payload ? (
        <div className="health-dashboard">
          <section className="health-summary panel" aria-labelledby="health-summary-title">
            <div className="health-summary__row">
              <HealthStatusDot tone={overallOk ? "success" : "danger"} />
              <div>
                <h2 id="health-summary-title" className="health-summary__title">
                  {overallOk ? "All systems operational" : "Attention required"}
                </h2>
                <p className="health-summary__desc muted">
                  {overallOk
                    ? "Every dependency reported a successful check."
                    : "One or more dependencies did not pass the latest check. Review the cards below."}
                </p>
              </div>
              <span className={`health-summary__pill ${overallOk ? "health-summary__pill--ok" : "health-summary__pill--warn"}`}>
                {overallOk ? "Operational" : "Degraded"}
              </span>
            </div>
            {payload.request_id ? (
              <p className="health-summary__rid muted">
                Request reference: <code>{String(payload.request_id)}</code>
              </p>
            ) : null}
          </section>

          <div className="health-grid" role="list">
            {orderedHealthDepKeys(payload.deps).map((key) => (
              <div key={key} role="listitem">
                <ServiceHealthCard depKey={key} title={healthServiceTitle(key)} dep={payload.deps[key]} />
              </div>
            ))}
          </div>

          {rawBody ? (
            <details className="health-technical panel">
              <summary>Technical details (JSON)</summary>
              <pre className="health-technical__pre">{rawBody}</pre>
            </details>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
