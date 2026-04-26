# Shared Python base with uv installed.
FROM python:3.11-slim AS python-base

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:$PATH"

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv-installer \
    curl -LsSf https://astral.sh/uv/install.sh | sh


# Stage 1: Backend dependencies and source
FROM python-base AS backend

ENV UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

COPY backend/pyproject.toml backend/uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY backend/ .


# Stage 2: Frontend build
FROM node:20-alpine AS frontend

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json* ./

RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY frontend/src ./src
COPY frontend/index.html .
COPY frontend/vite.config.ts .
COPY frontend/tsconfig.json .
COPY frontend/tsconfig.node.json .
COPY frontend/postcss.config.js .
COPY frontend/tailwind.config.js .

RUN npm run build


# Stage 3: Final runtime image
FROM python:3.11-slim AS runtime

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    curl \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    libice6 \
    && rm -rf /var/lib/apt/lists/*

ENV DOTENVX_VERSION=1.61.1
RUN curl -SsfL https://github.com/dotenvx/dotenvx/releases/download/v${DOTENVX_VERSION}/dotenvx-${DOTENVX_VERSION}-linux-x86_64.tar.gz \
    -o /tmp/dotenvx.tar.gz \
    && tar xzf /tmp/dotenvx.tar.gz -C /usr/local/bin --strip-components=1 ./dotenvx \
    && rm /tmp/dotenvx.tar.gz \
    && dotenvx --version

COPY --from=backend /app /app
ENV PATH="/app/.venv/bin:$PATH"
ENV HF_HOME="/app/model-cache/huggingface"

COPY --from=frontend /app/frontend/dist /app/frontend/dist

RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m appuser && \
    mkdir -p /app/data /app/model-cache && \
    chown -R appuser:appgroup /app/data /app/model-cache /app/frontend/dist && \
    chmod +x /app/scripts/validate_dotenvx.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=600s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

USER appuser

WORKDIR /app
CMD ["dotenvx", "run", "--", "sh", "-c", "scripts/validate_dotenvx.sh && python -m database.migrations && (python scripts/prewarm_docling_extract.py || true) && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
