import type { Role } from "../api/types";

/** Human-readable access level for UI copy (matches API `role`). */
export const ROLE_LABELS: Record<Role, string> = {
  admin: "Administrator",
  reviewer: "Reviewer",
  auditor: "Auditor",
};
