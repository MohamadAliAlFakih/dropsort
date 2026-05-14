/**
 * API path constants aligned with `app/main.py` router mounts and `app/api/*.py`.
 * All paths are absolute from the API root (no `/api` prefix here — that lives in
 * `VITE_API_BASE_URL` when using the Vite dev proxy).
 */

export const routes = {
  health: "/health",

  /** fastapi_users JWT router mounted at `/auth` + `/jwt`. */
  authJwtLogin: "/auth/jwt/login",

  me: "/me",

  batches: "/batches",
  batchDetail: (batchId: string) => `/batches/${batchId}`,

  predictionsRecent: "/predictions/recent",
  predictionDetail: (predictionId: string) => `/predictions/${predictionId}`,

  adminUsers: "/admin/users",
  adminUsersInvite: "/admin/users/invite",
  adminUser: (targetUserId: string) => `/admin/users/${targetUserId}`,
  adminUserRole: (targetUserId: string) => `/admin/users/${targetUserId}/role`,
  adminUserActive: (targetUserId: string) => `/admin/users/${targetUserId}/active`,

  audit: "/audit",
} as const;
