import { useState } from "react";
import { apiFetch } from "../api/client";
import { getNetworkErrorMessage } from "../api/httpErrors";
import { ErrorAlert } from "../components/ErrorAlert";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { useApiErrorHandler } from "../hooks/useApiErrorHandler";

type HealthJson = { status?: string };

export  function HomePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const assertOk = useApiErrorHandler({ redirectOnAuthErrors: false });

  async function checkHealth() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiFetch("/health", { auth: false });
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
    <main>
      <h1>Home</h1>
      <p className="muted">
        Calls <code>GET /health</code> on the API base URL from{" "}
        <code>VITE_API_BASE_URL</code>.
      </p>
      <p>
        <button type="button" onClick={checkHealth} disabled={loading}>
          {loading ? "Checking…" : "Check API health"}
        </button>
      </p>
      {loading ? <LoadingSpinner label="Contacting API…" /> : null}
      <ErrorAlert message={error} />
      {result ? <pre>{result}</pre> : null}
    </main>
  );
}