import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch, pathWithQuery } from "../api/client";
import { routes } from "../api/routes";
import type { BatchOut, PredictionOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Button } from "../components/Button";
import { PageSection } from "../components/data";
import { ErrorAlert } from "../components/ErrorAlert";
import { PageHeader } from "../components/PageHeader";
import { ROLE_LABELS } from "../lib/roleLabels";

const STATS_BATCH_LOOKBACK = 100;
const STATS_PREDICTION_LOOKBACK = 100;

type ModelCard = {
  backbone: string;
  weights_enum: string;
  freeze_policy: string;
  num_classes: number;
  class_names: string[];
  weights_sha256: string;
  weights_size_mb: number;
  metrics: {
    test_top1: number;
    test_top5: number;
    test_top1_golden: number;
    per_class: Record<string, number>;
    worst_class: string;
    worst_class_acc: number;
  };
  training: {
    epochs: number;
    batch_size: number;
    optimizer: string;
  };
  dataset: {
    name: string;
    splits: { train: number; validation: number; test: number };
  };
};

function isToday(iso: string): boolean {
  const d = new Date(iso);
  const now = new Date();
  return (
    d.getUTCFullYear() === now.getUTCFullYear() &&
    d.getUTCMonth() === now.getUTCMonth() &&
    d.getUTCDate() === now.getUTCDate()
  );
}

function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

function SignedOutHome() {
  return (
    <div className="page page--narrow">
      <PageHeader
        title="Welcome to Dropsort"
        description="Automatic document classification for your team. Sign in to view batches, recent predictions, and team activity."
        actions={
          <Link to="/login">
            <Button type="button">Sign in</Button>
          </Link>
        }
      />
    </div>
  );
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="stat-card panel">
      <div className="stat-card__label">{label}</div>
      <div className="stat-card__value">{value}</div>
      {hint ? <div className="stat-card__hint muted">{hint}</div> : null}
    </div>
  );
}

function ClassAccuracyChart({ perClass }: { perClass: Record<string, number> }) {
  const sorted = useMemo(
    () =>
      Object.entries(perClass).sort((a, b) => b[1] - a[1]),
    [perClass],
  );
  return (
    <div className="class-acc">
      {sorted.map(([cls, acc]) => (
        <div className="class-acc__row" key={cls}>
          <div className="class-acc__name">{cls}</div>
          <div className="class-acc__bar-wrap">
            <div
              className="class-acc__bar"
              style={{ width: `${(acc * 100).toFixed(1)}%` }}
              aria-label={`${cls}: ${pct(acc)}`}
            />
          </div>
          <div className="class-acc__val">{pct(acc)}</div>
        </div>
      ))}
    </div>
  );
}

export function HomePage() {
  const { token, me, meLoading } = useAuth();

  const [batches, setBatches] = useState<BatchOut[] | null>(null);
  const [predictions, setPredictions] = useState<PredictionOut[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [card, setCard] = useState<ModelCard | null>(null);
  const [cardError, setCardError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const [bRes, pRes] = await Promise.all([
        apiFetch(pathWithQuery(routes.batches, { offset: 0, limit: STATS_BATCH_LOOKBACK })),
        apiFetch(pathWithQuery(routes.predictionsRecent, { limit: STATS_PREDICTION_LOOKBACK })),
      ]);
      if (bRes.ok) setBatches((await bRes.json()) as BatchOut[]);
      else setBatches([]);
      if (pRes.ok) setPredictions((await pRes.json()) as PredictionOut[]);
      else setPredictions([]);
    } catch {
      setLoadError("Could not load workspace stats.");
    }
  }, []);

  useEffect(() => {
    if (!token) return;
    void load();
  }, [token, load]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/model_card.json");
        if (!res.ok) {
          if (!cancelled) setCardError("Model card not available.");
          return;
        }
        const data = (await res.json()) as ModelCard;
        if (!cancelled) setCard(data);
      } catch {
        if (!cancelled) setCardError("Model card not available.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!token) {
    return <SignedOutHome />;
  }

  const greetingName = me?.email ? me.email.split("@")[0] : "there";
  const role = me && !meLoading ? ROLE_LABELS[me.role] : null;

  const batchesToday = batches ? batches.filter((b) => isToday(b.updated_at)).length : 0;
  const predictionsToday = predictions
    ? predictions.filter((p) => isToday(p.created_at)).length
    : 0;
  const reviewerCorrections = predictions
    ? predictions.filter((p) => Boolean(p.relabel_label)).length
    : 0;

  return (
    <div className="page">
      <PageHeader
        title={`Welcome back, ${greetingName}`}
        description={role ? `Signed in as ${role}.` : "Workspace overview."}
      />

      <ErrorAlert message={loadError} />

      <div className="stats-grid">
        <StatCard label="Batches today" value={String(batchesToday)} hint="Last 100 batches sample" />
        <StatCard
          label="Predictions today"
          value={String(predictionsToday)}
          hint="Last 100 predictions sample"
        />
        <StatCard
          label="Model top-1 accuracy"
          value={card ? pct(card.metrics.test_top1) : "..."}
          hint={card ? `Top-5: ${pct(card.metrics.test_top5)}` : undefined}
        />
        <StatCard
          label="Reviewer corrections"
          value={String(reviewerCorrections)}
          hint="In recent predictions"
        />
      </div>

      <PageSection title="Model card" description="Snapshot of the deployed classifier.">
        {card ? (
          <div className="model-card-grid">
            <div className="panel model-card-panel">
              <dl className="model-card-dl">
                <dt>Backbone</dt>
                <dd>{card.backbone}</dd>
                <dt>Weights enum</dt>
                <dd>{card.weights_enum}</dd>
                <dt>Freeze policy</dt>
                <dd>{card.freeze_policy}</dd>
                <dt>Optimizer</dt>
                <dd>
                  {card.training.optimizer} (epochs {card.training.epochs}, batch {card.training.batch_size})
                </dd>
                <dt>Dataset</dt>
                <dd>
                  {card.dataset.name} (train {card.dataset.splits.train.toLocaleString()}, test{" "}
                  {card.dataset.splits.test.toLocaleString()})
                </dd>
                <dt>Weights size</dt>
                <dd>{card.weights_size_mb.toFixed(1)} MB</dd>
                <dt>SHA-256</dt>
                <dd>
                  <code className="muted">{card.weights_sha256.slice(0, 16)}...</code>
                </dd>
                <dt>Worst class</dt>
                <dd>
                  {card.metrics.worst_class} ({pct(card.metrics.worst_class_acc)})
                </dd>
              </dl>
            </div>
            <div className="panel model-card-panel">
              <div className="model-card-section-title">
                Supported document types ({card.num_classes})
              </div>
              <div className="label-chips">
                {card.class_names.map((name) => (
                  <span className="label-chip" key={name}>
                    {name}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </PageSection>

      <PageSection
        title="Per-class accuracy"
        description="For each of the 16 document types, this is how often the model gets it right on the held-out test set. Higher = stronger; lower = the model often confuses that type with others."
      >
        {cardError ? <ErrorAlert message={cardError} /> : null}
        {card ? <ClassAccuracyChart perClass={card.metrics.per_class} /> : null}
      </PageSection>
    </div>
  );
}
