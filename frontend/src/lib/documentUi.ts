import type { BatchState } from "../api/types";

/** Matches `StatusBadge` tone prop (avoid importing component into pure helpers). */
export type BatchBadgeTone = "neutral" | "info" | "success" | "warning" | "danger";

export function batchStateLabel(state: BatchState): string {
  const labels: Record<BatchState, string> = {
    received: "Received",
    processing: "Processing",
    complete: "Complete",
    failed: "Failed",
  };
  return labels[state];
}

export function batchStateTone(state: BatchState): BatchBadgeTone {
  switch (state) {
    case "complete":
      return "success";
    case "failed":
      return "danger";
    case "processing":
      return "warning";
    case "received":
      return "info";
  }
}

export type ConfidenceTier = "high" | "medium" | "low";

/** Visual bands for model confidence (readability only; not a business rule). */
export function confidenceTier(value: number): ConfidenceTier {
  if (value >= 0.85) {
    return "high";
  }
  if (value >= 0.5) {
    return "medium";
  }
  return "low";
}

export function confidenceTierDescription(tier: ConfidenceTier): string {
  switch (tier) {
    case "high":
      return "High confidence (about 0.85 or above)";
    case "medium":
      return "Medium confidence (about 0.50–0.84)";
    case "low":
      return "Low confidence (below about 0.50)";
  }
}
