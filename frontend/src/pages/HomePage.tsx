import { useState } from "react";
import { apiFetch } from "../api/client";

type HealthJson = { status?: string };

export function HomePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function checkHealth() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiFetch("/health", { auth: false });
      const text = await res.text();
      if (!res.ok) {
        setError(`HTTP ${res.status}: ${text || res.statusText}`);
        return;
      }
      let display = text;
      try {
        const json = JSON.parse(text) as HealthJson;
        display = JSON.stringify(json, null, 2);
      } catch {
        /* not JSON — show raw text */
      }
      setResult(display);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
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
      {error ? <p className="error">{error}</p> : null}
      {result ? <pre>{result}</pre> : null}
    </main>
  );
}