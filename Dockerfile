# Stage 1: Backend
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy backend pyproject.toml and install dependencies
COPY backend/pyproject.toml backend/ .
RUN uv sync --frozen --no-dev

# Copy backend code
COPY backend/ .

# Stage 2: Frontend
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

# Stage 3: Final
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for running the application
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Copy backend virtual environment from stage 1
COPY --from=backend /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy backend code from stage 1
COPY --from=backend /app /app

# Copy frontend build from stage 2
COPY --from=frontend /app/frontend/dist /app/frontend/dist

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Initialize database and start application
CMD ["sh", "-c", "uv run python -m database.migrations && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
