import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import {
  ApiHttpError,
  ForbiddenNavigationError,
  UnauthorizedSessionError,
} from "../api/httpErrors";

export type UseApiErrorHandlerOptions = {
  /**
   * When true (default), 401 clears the session and 403 routes to /forbidden.
   * Set false for anonymous/public requests (e.g. health checks) so 401/403 are ordinary errors.
   */
  redirectOnAuthErrors?: boolean;
};

/**
 * Returns a function that throws on non-OK responses (after optional redirects).
 * On success, returns the same Response for optional body parsing by the caller.
 */
export function useApiErrorHandler(
  options: UseApiErrorHandlerOptions = {},
) {
  const { redirectOnAuthErrors = true } = options;
  const navigate = useNavigate();
  const { logout } = useAuth();

  return useCallback(
    async (res: Response): Promise<Response> => {
      if (res.ok) {
        return res;
      }

      if (redirectOnAuthErrors && res.status === 401) {
        logout();
        navigate("/login", { replace: true });
        throw new UnauthorizedSessionError();
      }

      if (redirectOnAuthErrors && res.status === 403) {
        navigate("/forbidden", { replace: true });
        throw new ForbiddenNavigationError();
      }

      const text = await res.text().catch(() => "");
      throw new ApiHttpError(res.status, text || res.statusText);
    },
    [logout, navigate, redirectOnAuthErrors],
  );
}