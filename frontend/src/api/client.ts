import { getToken } from "../auth/tokenStorage";

/**
 * Base URL for API calls: absolute origin (e.g. `http://127.0.0.1:8000`) or same-origin
 * prefix for Vite dev proxy (e.g. `/api`). Trailing slashes are stripped; `path` must
 * start with `/` so joins are `/api` + `/health` → `/api/health`.
 */
function requireBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL;
  if (typeof base !== "string" || base.trim() === "") {
    throw new Error(
      "Missing VITE_API_BASE_URL. Copy frontend/.env.example to frontend/.env (dev: `/api` with Vite proxy; prod: full API origin).",
    );
  }
  return base.replace(/\/+$/, "");
}

/** Join base URL and path (path must start with `/`). */
export function apiUrl(path: string): string {
  const base = requireBaseUrl();
  if (!path.startsWith("/")) {
    throw new Error(`apiUrl path must start with "/": ${path}`);
  }
  if (base === "") {
    return path;
  }
  return `${base}${path}`;
}

export type ApiFetchOptions = RequestInit & {
  /** When false, do not send Authorization. Default true. */
  auth?: boolean;
};

export async function apiFetch(
  path: string,
  init: ApiFetchOptions = {},
): Promise<Response> {
  const { auth = true, headers: initHeaders, ...rest } = init;
  const headers = new Headers(initHeaders);

  if (auth) {
    const token = getToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  return fetch(apiUrl(path), { ...rest, headers });
}
