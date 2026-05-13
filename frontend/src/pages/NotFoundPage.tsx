import { NavLink } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";

export  function NotFoundPage() {
  return (
    <div className="page">
      <PageHeader title="Not found" />
      <EmptyState
        title="Page not found"
        description="No page matches this URL."
      >
        <NavLink to="/" className="inline-link" end>
          Back to home
        </NavLink>
      </EmptyState>
    </div>
  );
}