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
  
  export function getNetworkErrorMessage(error: unknown): string {
    if (
      error instanceof UnauthorizedSessionError ||
      error instanceof ForbiddenNavigationError
    ) {
      return "";
    }
    if (error instanceof ApiHttpError) {
      const trimmed = error.message.trim();
      if (trimmed.length > 0) {
        return `Request failed (${error.status}): ${trimmed}`;
      }
      return `Request failed (${error.status}).`;
    }
    if (error instanceof TypeError) {
      return "Network error — check your connection and API base URL.";
    }
    if (error instanceof Error) {
      return error.message;
    }
    return "Something went wrong.";
  }