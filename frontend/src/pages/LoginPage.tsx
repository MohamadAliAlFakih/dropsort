import { Link, useLocation } from "react-router-dom";
import { Button } from "../components/Button";
import { PageHeader } from "../components/PageHeader";

type LoginLocationState = {
  from?: { pathname: string; search?: string };
};

export function LoginPage() {
  const location = useLocation();
  const state = location.state as LoginLocationState | null;
  const from = state?.from;

  return (
    <div className="page">
      <PageHeader
        title="Login"
        description="Authentication is not wired yet. When the API exposes login, this page will submit credentials and store the JWT using the shared auth helpers."
      />

      {from ? (
        <p className="muted" role="status">
          Sign in to access the page you opened.{" "}
          <Link className="inline-link" to={`${from.pathname}${from.search ?? ""}`}>
            Go back
          </Link>
        </p>
      ) : null}

      <form
        className="auth-form panel"
        onSubmit={(e) => {
          e.preventDefault();
        }}
      >
        <div className="form-field">
          <label htmlFor="email">Email</label>
          <input id="email" name="email" type="email" autoComplete="username" />
        </div>
        <div className="form-field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
          />
        </div>
        <div className="form-field">
          <Button type="submit" disabled>
            Sign in (disabled)
          </Button>
        </div>
      </form>
    </div>
  );
}
