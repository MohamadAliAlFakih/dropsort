import { getToken } from "../auth/tokenStorage";

function requireBaseUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL;
  if (typeof base !== "string" || base.trim() === "") {
    throw new Error(
      "Missing VITE_API_BASE_URL. Copy frontend/.env.example to frontend/.env and set the API origin.",
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