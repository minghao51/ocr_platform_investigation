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

# Copy only dependency metadata first so backend dependency installs are cached.
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

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
FROM python-base AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code and virtual environment from stage 1
COPY --from=backend /app /app
ENV PATH="/app/.venv/bin:$PATH"

# Copy frontend build from stage 2
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Initialize database and start application
CMD ["sh", "-c", "python -m database.migrations && uvicorn main:app --host 0.0.0.0 --port 8000"]
