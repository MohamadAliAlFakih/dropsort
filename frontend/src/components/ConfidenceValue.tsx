import { confidenceTier, confidenceTierDescription } from "../lib/documentUi";

export type ConfidenceValueProps = {
  value: number;
};

/**
 * Displays top-1 (or similar) confidence with color bands for quick scanning.
 */
export function ConfidenceValue({ value }: ConfidenceValueProps) {
  const tier = confidenceTier(value);
  const text = value.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
  return (
    <span className={`confidence-value confidence-value--${tier}`} title={confidenceTierDescription(tier)}>
      {text}
    </span>
  );
}
