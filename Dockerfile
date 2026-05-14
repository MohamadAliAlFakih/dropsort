# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.11

# ---------- Builder ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_NO_CACHE=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get clean && rm -rf /var/lib/apt/lists/* && \
    apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first
COPY pyproject.toml uv.lock* ./

# Install dependencies
RUN uv sync --frozen --no-dev || uv sync --no-dev

# Copy source code
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./alembic.ini

# Install project
RUN uv pip install --system -e .

# ---------- Runtime ----------
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DROPSORT_MODE=api \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get clean && rm -rf /var/lib/apt/lists/* && \
    apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends \
        libgomp1 \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home --uid 1001 dropsort

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

RUN chown -R dropsort:dropsort /app

USER dropsort

EXPOSE 8000

CMD ["sh", "-c", "case \"$DROPSORT_MODE\" in \
  api) exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ;; \
  worker) exec python -m app.workers.inference_worker ;; \
  sftp-ingest) exec python -m app.workers.sftp_ingest ;; \
  migrate) exec alembic upgrade head ;; \
  *) echo \"Unknown DROPSORT_MODE='$DROPSORT_MODE'\" >&2; exit 1 ;; \
esac"]