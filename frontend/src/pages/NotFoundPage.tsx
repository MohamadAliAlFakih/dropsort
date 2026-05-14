import { NavLink } from "react-router-dom";
import { EmptyState } from "../components/EmptyState";
import { PageHeader } from "../components/PageHeader";

export function NotFoundPage() {
  return (
    <div className="page page--narrow">
      <PageHeader title="Page not found" description="That address does not match any screen in this app." />
      <EmptyState
        title="Nothing here"
        description="Double-check the URL, or head home and navigate from the menu."
      >
        <NavLink to="/" className="inline-link" end>
          Back to home
        </NavLink>
      </EmptyState>
    </div>
  );
}
