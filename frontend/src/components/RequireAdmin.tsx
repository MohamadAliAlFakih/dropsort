import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LoadingSpinner } from "./LoadingSpinner";

type RequireAdminProps = {
  children: ReactNode;
};

/**
 * Requires an authenticated user whose role is `admin`.
 * Must be used under a route that already requires a session (e.g. with RequireAuth).
 */
export function RequireAdmin({ children }: RequireAdminProps) {
  const { token, me, meLoading } = useAuth();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (meLoading && !me) {
    return (
      <div className="page">
        <LoadingSpinner label="Checking permissions…" />
      </div>
    );
  }

  if (!me) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (me.role !== "admin") {
    return <Navigate to="/forbidden" replace />;
  }

  return <>{children}</>;
}
