/**
 * Shapes returned by GET /health (`app/api/health.py`).
 * Used only for presentation — keep in sync when the backend adds fields.
 */

export type HealthDepCheck = {
  status: string;
  latency_ms?: number;
  error?: string;
  policy_count?: number;
};

export type HealthPayload = {
  ok: boolean;
  request_id?: string | null;
  deps: Record<string, HealthDepCheck>;
};

/** Preferred card order; unknown keys from the API are appended after. */
export const HEALTH_SERVICE_ORDER = [
  "postgres",
  "redis",
  "vault",
  "casbin_policy",
  "minio",
  "classifier",
] as const;

export function healthServiceTitle(key: string): string {
  switch (key) {
    case "postgres":
      return "PostgreSQL";
    case "redis":
      return "Redis";
    case "vault":
      return "Vault";
    case "casbin_policy":
      return "Access policy";
    case "minio":
      return "Object storage (MinIO)";
    case "classifier":
      return "Classifier weights";
    default:
      return key.replace(/_/g, " ");
  }
}

export function isHealthPayload(value: unknown): value is HealthPayload {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const o = value as Record<string, unknown>;
  if (typeof o.ok !== "boolean" || o.deps === null || typeof o.deps !== "object") {
    return false;
  }
  const deps = o.deps as Record<string, unknown>;
  for (const v of Object.values(deps)) {
    if (typeof v !== "object" || v === null) {
      return false;
    }
    const d = v as Record<string, unknown>;
    if (typeof d.status !== "string") {
      return false;
    }
  }
  return true;
}

export function orderedHealthDepKeys(deps: Record<string, HealthDepCheck>): string[] {
  const keys = Object.keys(deps);
  const ordered: string[] = [];
  for (const k of HEALTH_SERVICE_ORDER) {
    if (keys.includes(k)) {
      ordered.push(k);
    }
  }
  for (const k of keys) {
    if (!ordered.includes(k)) {
      ordered.push(k);
    }
  }
  return ordered;
}
