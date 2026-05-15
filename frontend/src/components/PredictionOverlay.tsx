import { useEffect, useState } from "react";
import { apiFetch } from "../api/client";
import { routes } from "../api/routes";

type Props = {
  predictionId: string;
  filename: string;
  hasOverlay: boolean;
};

export function PredictionOverlay({ predictionId, filename, hasOverlay }: Props) {
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasOverlay) {
      return;
    }
    let cancelled = false;
    let objectUrl: string | null = null;

    (async () => {
      try {
        const res = await apiFetch(routes.predictionOverlay(predictionId));
        if (!res.ok) {
          if (!cancelled) {
            setError("Preview unavailable");
          }
          return;
        }
        const blob = await res.blob();
        objectUrl = URL.createObjectURL(blob);
        if (!cancelled) {
          setUrl(objectUrl);
        } else {
          URL.revokeObjectURL(objectUrl);
        }
      } catch {
        if (!cancelled) {
          setError("Preview unavailable");
        }
      }
    })();

    return () => {
      cancelled = true;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [predictionId, hasOverlay]);

  if (!hasOverlay) {
    return <span className="prediction-overlay prediction-overlay--empty muted">No preview</span>;
  }
  if (error) {
    return <span className="prediction-overlay prediction-overlay--empty muted">{error}</span>;
  }
  if (!url) {
    return <span className="prediction-overlay prediction-overlay--loading" aria-label="Loading preview" />;
  }
  return (
    <a className="prediction-overlay" href={url} target="_blank" rel="noopener noreferrer">
      <img className="prediction-overlay__img" src={url} alt={`Overlay preview for ${filename}`} />
    </a>
  );
}
