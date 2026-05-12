# syntax=docker/dockerfile:1.7
# dropsort single backend image - one build, four invocations (api / worker / sftp-ingest / migrate).
# Per CONTEXT D-02. The selected mode is read from the DROPSORT_MODE env var.

ARG PYTHON_VERSION=3.11

# ---------- Builder ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install uv (matches CONTEXT D-08).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Cache deps before copying app code so reinstalls only happen when pyproject changes.
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy application source.
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

# Install the project itself into site-packages.
RUN uv pip install --system -e .

# ---------- Runtime ----------
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DROPSORT_MODE=api

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1001 dropsort

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN chown -R dropsort:dropsort /app
USER dropsort

EXPOSE 8000
# Phase 1: api branch uses uvicorn directly; worker/sftp-ingest/migrate use `python -m`
# / `alembic`. Phase 4 fills worker bodies; Phase 5 may refine these CMD lines further.
CMD ["sh", "-c", "case \"$DROPSORT_MODE\" in \
  api) exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ;; \
  worker) exec python -m app.workers.inference ;; \
  sftp-ingest) exec python -m app.workers.sftp_ingest ;; \
  migrate) exec alembic upgrade head ;; \
  *) echo \"Unknown DROPSORT_MODE='$DROPSORT_MODE' (expected: api | worker | sftp-ingest | migrate)\" >&2; exit 1 ;; \
esac"]
