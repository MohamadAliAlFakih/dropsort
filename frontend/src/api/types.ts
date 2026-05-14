/**
 * JSON-friendly TypeScript shapes mirroring `app/domain/*.py` (+ batch detail envelope
 * from `app/api/batches.py`). Datetimes are `string` (ISO 8601 from the API).
 */

/** `app/domain/user.py` — Role */
export type Role = "admin" | "reviewer" | "auditor";

/** `app/domain/user.py` — UserOut */
export type UserOut = {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
  /** ISO 8601 when the account was soft-deleted (admin directory removal). */
  deleted_at?: string | null;
  /** Real address before removal; internal `email` becomes a placeholder after soft-delete. */
  original_email?: string | null;
};

/** `app/domain/user.py` — UserCreate (POST /admin/users/invite) */
export type UserCreate = {
  email: string;
  initial_secret: string;
  role: Role;
};

/** `app/domain/user.py` — RoleChangeIn */
export type RoleChangeIn = {
  role: Role;
};

/** `app/domain/user.py` — UserActiveIn */
export type UserActiveIn = {
  is_active: boolean;
};

/** `app/domain/batch.py` — BatchState */
export type BatchState = "received" | "processing" | "complete" | "failed";

/** `app/domain/batch.py` — BatchOut */
export type BatchOut = {
  id: string;
  external_id: string | null;
  state: BatchState;
  created_at: string;
  updated_at: string;
  prediction_count: number;
};

/** `app/domain/prediction.py` — TopKItem */
export type TopKItem = {
  label: string;
  score: number;
};

/** `app/domain/prediction.py` — PredictionOut */
export type PredictionOut = {
  id: string;
  batch_id: string;
  filename: string;
  label: string;
  top1_confidence: number;
  top5: TopKItem[];
  minio_overlay_key: string | null;
  relabel_label: string | null;
  relabel_actor_id: string | null;
  relabel_at: string | null;
  created_at: string;
};

/** `app/domain/prediction.py` — PredictionRelabelIn (PATCH /predictions/{id} body) */
export type PredictionRelabelIn = {
  label: string;
};

/** `app/api/batches.py` — BatchDetail response_model */
export type BatchDetail = {
  batch: BatchOut;
  predictions: PredictionOut[];
};

/** `app/domain/audit.py` — AuditEntryOut */
export type AuditEntryOut = {
  id: string;
  actor_id: string;
  /** Enriched on GET /audit for display (email or removed-account label). */
  actor_email?: string | null;
  action: string;
  target_type: string;
  target_id: string;
  /** Enriched human-readable subject line (email, filename, batch label, etc.). */
  target_label?: string | null;
  created_at: string;
  metadata_jsonb: Record<string, unknown> | null;
};

/** fastapi-users JWT `POST /auth/jwt/login` success body (see fastapi-users auth router). */
export type JwtLoginResponse = {
  access_token: string;
  token_type: string;
};
