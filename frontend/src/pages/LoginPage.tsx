import { Link, useLocation } from "react-router-dom";

export  function LoginPage() {
  const location = useLocation();
  const from = (location.state as { from?: Location } | null)?.from;

  return (
    <main>
      <h1>Login</h1>
      {from ? (
        <p className="muted" role="status">
          Sign in to access the page you opened.{" "}
          <Link to={from.pathname + (from.search ?? "")}>Go back</Link>
        </p>
      ) : null}
      <p className="muted">
        Authentication is not wired yet. When the API exposes login, this page
        will submit credentials and store the JWT using the shared auth helpers.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
        }}
      >
        <p>
          <label htmlFor="email">Email</label>
          <br />
          <input id="email" name="email" type="email" autoComplete="username" />
        </p>
        <p>
          <label htmlFor="password">Password</label>
          <br />
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
          />
        </p>
        <p>
          <button type="submit" disabled>
            Sign in (disabled)
          </button>
        </p>
      </form>
    </main>
  );
}