import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import type { JwtLoginResponse } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { loginWithPassword } from "../auth/login";
import { Button } from "../components/Button";
import { ErrorAlert } from "../components/ErrorAlert";
import { PageHeader } from "../components/PageHeader";

type LoginLocationState = {
  from?: { pathname: string; search?: string };
};

function parseJwtLoginBody(raw: unknown): JwtLoginResponse | null {
  if (typeof raw !== "object" || raw === null) {
    return null;
  }
  const o = raw as Record<string, unknown>;
  if (typeof o.access_token !== "string" || typeof o.token_type !== "string") {
    return null;
  }
  return { access_token: o.access_token, token_type: o.token_type };
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as LoginLocationState | null;
  const from = state?.from;

  const { token, setToken } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (token) {
      navigate(from ? `${from.pathname}${from.search ?? ""}` : "/me", {
        replace: true,
      });
    }
  }, [token, from, navigate]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await loginWithPassword(email, password);
      const text = await res.text();
      let body: unknown;
      try {
        body = text ? JSON.parse(text) : null;
      } catch {
        body = null;
      }

      if (!res.ok) {
        const detail = (body as { detail?: unknown } | null)?.detail;
        const msg =
          typeof detail === "string"
            ? detail
            : detail !== undefined
              ? JSON.stringify(detail)
              : text || `HTTP ${res.status}`;
        setError(msg);
        return;
      }

      const parsed = parseJwtLoginBody(body);
      if (!parsed) {
        setError("Login response missing access_token.");
        return;
      }

      setToken(parsed.access_token);
      navigate(from ? `${from.pathname}${from.search ?? ""}` : "/me", {
        replace: true,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  if (token) {
    return null;
  }

  return (
    <div className="page">
      <PageHeader
        title="Login"
        description="Sign in with the email and password issued by an administrator."
      />

      {from ? (
        <p className="muted" role="status">
          Sign in to access the page you opened.{" "}
          <Link className="inline-link" to={`${from.pathname}${from.search ?? ""}`}>
            Go back
          </Link>
        </p>
      ) : null}

      <form className="auth-form panel" onSubmit={onSubmit}>
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(ev) => setEmail(ev.target.value)}
            required
          />
        </div>
        <div className="form-field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(ev) => setPassword(ev.target.value)}
            required
          />
        </div>
        <ErrorAlert message={error} />
        <div className="form-field">
          <Button type="submit" disabled={submitting}>
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </div>
      </form>
    </div>
  );
}
