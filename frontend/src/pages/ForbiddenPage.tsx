import { NavLink } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";

export  function ForbiddenPage() {
  return (
    <div className="page">
      <PageHeader title="Access denied" />
      <EmptyState
        title="Forbidden"
        description="You do not have permission to view this resource (HTTP 403)."
      >
        <NavLink to="/" className="inline-link" end>
          Back to home
        </NavLink>
      </EmptyState>
    </div>
  );
}