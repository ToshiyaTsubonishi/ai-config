FROM python:3.13-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN python -m pip install --upgrade pip \
    && python -m pip install .

RUN ai-config-vendor-skills --repo-root /app sync-manifest \
    && ai-config-index --repo-root /app --profile default

RUN find /app/skills -type d -name .git -prune -exec rm -rf {} +


FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

COPY --from=builder /usr/local /usr/local
COPY --from=builder /app/config /app/config
COPY --from=builder /app/skills /app/skills
COPY --from=builder /app/.index /app/.index

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

CMD ["ai-config-selector-serving", "--repo-root", "/app", "--index-dir", "/app/.index"]
