# Shared Python base with uv installed.
FROM python:3.11-slim AS python-base

WORKDIR /app
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh


# Stage 1: Backend dependencies and source
FROM python-base AS backend

ENV UV_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

COPY backend/pyproject.toml backend/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copy backend code
COPY backend/ .


# Stage 2: Frontend build
FROM node:20-alpine AS frontend

WORKDIR /app/frontend

# Copy frontend package files separately for better caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy frontend source code
COPY frontend/src ./src
COPY frontend/index.html .
COPY frontend/vite.config.ts .
COPY frontend/tsconfig.json .
COPY frontend/tsconfig.node.json .
COPY frontend/postcss.config.js .
COPY frontend/tailwind.config.js .

# Build frontend
RUN npm run build


# Stage 3: Final runtime image
FROM python:3.11-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
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

# Install dotenvx (pinned version)
ENV DOTENVX_VERSION=1.61.1
RUN curl -SsfL https://github.com/dotenvx/dotenvx/releases/download/v${DOTENVX_VERSION}/dotenvx-${DOTENVX_VERSION}-linux-x86_64.tar.gz \
    -o /tmp/dotenvx.tar.gz \
    && tar xzf /tmp/dotenvx.tar.gz -C /usr/local/bin --strip-components=1 ./dotenvx \
    && rm /tmp/dotenvx.tar.gz \
    && dotenvx --version

# Copy backend code and virtual environment from stage 1
COPY --from=backend /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Copy frontend build from stage 2
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Create non-root user and data directory
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appgroup /app/data /app/frontend/dist

# Copy dotenvx validation script
COPY backend/scripts/validate_dotenvx.sh /app/backend/scripts/validate_dotenvx.sh
RUN chmod +x /app/backend/scripts/validate_dotenvx.sh

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run as non-root user
USER appuser

# Initialize database and start application
WORKDIR /app
CMD ["dotenvx", "run", "--", "sh", "-c", "backend/scripts/validate_dotenvx.sh && python -m database.migrations && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
