import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

type RequireAuthProps = {
  children: ReactNode;
};

export function RequireAuth({ children }: RequireAuthProps) {
  const { token } = useAuth();
  const location = useLocation();

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}