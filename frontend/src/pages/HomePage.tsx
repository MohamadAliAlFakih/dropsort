import { useState } from "react";
import { apiFetch } from "../api/client";
import { routes } from "../api/routes";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { Button } from "../components/Button";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { PageHeader } from "../components/PageHeader";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";

type HealthJson = { status?: string };

export function HomePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: false });

  async function checkHealth() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiFetch(routes.health, { auth: false });
      await assertOk(res);
      const text = await res.text();
      let display = text;
      try {
        const json = JSON.parse(text) as HealthJson;
        display = JSON.stringify(json, null, 2);
      } catch {
        /* not JSON — show raw text */
      }
      setResult(display);
    } catch (e) {
      setError(getNetworkErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <PageHeader
        title="Home"
        description="Calls GET /health (via `routes.health` + `VITE_API_BASE_URL`; dev uses `/api` + Vite proxy)."
        actions={
          <Button type="button" onClick={checkHealth} disabled={loading}>
            {loading ? "Checking…" : "Check API health"}
          </Button>
        }
      />

      {loading ? <LoadingSpinner label="Contacting API…" /> : null}
      <ErrorAlert message={error} />

      {result ? <pre>{result}</pre> : null}
    </div>
  );
}
