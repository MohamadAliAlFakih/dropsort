import { Link } from "react-router-dom";

export function ForbiddenPage() {
  return (
    <main>
      <h1>Access denied</h1>
      <p className="muted">
        You do not have permission to view this resource (HTTP 403).
      </p>
      <p>
        <Link to="/">Back to home</Link>
      </p>
    </main>
  );
}