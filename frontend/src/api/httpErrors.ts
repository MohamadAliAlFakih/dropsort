/** Thrown when the hook has already applied 401 side effects (logout + navigate). */
export class UnauthorizedSessionError extends Error {
  constructor() {
    super("Unauthorized");
    this.name = "UnauthorizedSessionError";
  }
}

/** Thrown when the hook has already navigated to /forbidden. */
export class ForbiddenNavigationError extends Error {
  constructor() {
    super("Forbidden");
    this.name = "ForbiddenNavigationError";
  }
}

/** Any other non-OK HTTP response (body stored as message when present). */
export class ApiHttpError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiHttpError";
    this.status = status;
  }
}

/**
 * Parse typical FastAPI error JSON (`{"detail": "..."}` or validation array) for display.
 */
export function messageFromFastApiBody(bodyText: string): string | null {
  const trimmed = bodyText.trim();
  if (!trimmed.startsWith("{")) {
    return null;
  }
  try {
    const parsed = JSON.parse(trimmed) as { detail?: unknown };
    const d = parsed.detail;
    if (typeof d === "string") {
      return d;
    }
    if (Array.isArray(d)) {
      const parts = d
        .map((item) => {
          if (typeof item !== "object" || item === null) {
            return String(item);
          }
          const loc =
            "loc" in item && Array.isArray((item as { loc?: unknown }).loc)
              ? (item as { loc: unknown[] }).loc.join(".")
              : "";
          const msg =
            "msg" in item && typeof (item as { msg?: unknown }).msg === "string"
              ? (item as { msg: string }).msg
              : JSON.stringify(item);
          return loc ? `${loc}: ${msg}` : msg;
        })
        .filter(Boolean);
      if (parts.length > 0) {
        return parts.join("; ");
      }
    }
  } catch {
    return null;
  }
  return null;
}

function messageForApiHttpError(error: ApiHttpError): string {
  const fromBody = messageFromFastApiBody(error.message);
  if (fromBody) {
    return `Request failed (${error.status}): ${fromBody}`;
  }
  const trimmed = error.message.trim();
  if (trimmed.length > 0) {
    return `Request failed (${error.status}): ${trimmed}`;
  }
  return `Request failed (${error.status}).`;
}

export function getNetworkErrorMessage(error: unknown): string {
  if (
    error instanceof UnauthorizedSessionError ||
    error instanceof ForbiddenNavigationError
  ) {
    return "";
  }
  if (error instanceof ApiHttpError) {
    return messageForApiHttpError(error);
  }
  if (error instanceof TypeError) {
    return "Network error — check your connection and API base URL.";
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong.";
}
