import { NavLink } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";

export function ForbiddenPage() {
  return (
    <div className="page page--narrow">
      <PageHeader title="Access restricted" />
      <EmptyState
        title="Not allowed"
        description="You are signed in, but this action is not permitted for your role."
      >
        <NavLink to="/" className="inline-link" end>
          Back to home
        </NavLink>
      </EmptyState>
    </div>
  );
}
