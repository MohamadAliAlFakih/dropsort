import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main>
      <h1>Not found</h1>
      <p className="muted">No page matches this URL.</p>
      <p>
        <Link to="/">Back to home</Link>
      </p>
    </main>
  );
}