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

function friendlyForStatus(status: number, fromBody: string | null): string {
  if (status === 400) {
    return fromBody ?? "That request was not valid. Please check your input and try again.";
  }
  if (status === 401) {
    return "Your session expired. Please sign in again.";
  }
  if (status === 403) {
    return "You don't have permission to do that.";
  }
  if (status === 404) {
    return "We couldn't find what you were looking for.";
  }
  if (status === 409) {
    return fromBody ?? "That conflicts with the current state. Refresh and try again.";
  }
  if (status === 413) {
    return "That file is too large to upload.";
  }
  if (status === 422) {
    return fromBody ?? "Some of the information you entered isn't valid.";
  }
  if (status === 429) {
    return "Too many requests. Please wait a moment and try again.";
  }
  if (status >= 500) {
    return "The server is having trouble right now. Please try again in a moment.";
  }
  return fromBody ?? "Something went wrong. Please try again.";
}

function messageForApiHttpError(error: ApiHttpError): string {
  const fromBody = messageFromFastApiBody(error.message);
  return friendlyForStatus(error.status, fromBody);
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
    return "Could not reach the server. Check your connection and try again.";
  }
  return "Something went wrong. Please try again.";
}
