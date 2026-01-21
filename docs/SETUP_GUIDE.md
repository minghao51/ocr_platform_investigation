# OCR Platform - Complete Setup Guide

This guide provides comprehensive instructions for setting up and running the OCR Platform MVP on your local machine.

**✨ Updated:** 2026-01-20 - Now uses `uv` for faster builds and automatic database initialization!

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Local Development Setup](#local-development-setup)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

#### 1. Docker & Docker Compose
**Why**: Required for containerized deployment and production-like environment.

**Installation**:
- **Mac**: Download [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- **Windows**: Download [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- **Linux**: Install via package manager
  ```bash
  # Ubuntu/Debian
  sudo apt-get update
  sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin
  ```

**Verify Installation**:
```bash
docker --version
# Should output: Docker version 27.x.x or higher
docker compose version
# Should output: Docker Compose version v2.x.x or higher
```

#### 2. API Keys for VLM Providers

You need API keys for at least one of these providers:

**Nebius (Llama 3.2 Vision)**:
- Sign up at: https://nebius.ai/
- Get API key from: https://nebius.ai/dashboard/api-keys
- Free tier available for testing

**OpenRouter (Claude, GPT-4o, Gemini)**:
- Sign up at: https://openrouter.ai/
- Get API key from: https://openrouter.ai/keys
- Pay-as-you-go, starts at $5

**Google Gemini 1.5**:
- Sign up at: https://ai.google.dev/
- Get API key from: https://ai.google.dev/api
- Free tier: 15 requests/minute for Gemini Flash

**💡 Recommendation**: Start with Google Gemini (free tier) or Nebius (free credits) for testing.

---

## Quick Start (Docker)

This is the **recommended method** for most users. Docker handles all dependencies automatically.

### Step 1: Clone or Navigate to Project

```bash
cd /path/to/ocr_platform_testdrive
```

### Step 2: Configure Environment Variables

```bash
# Copy the environment template
cp .env.example .env
```

### Step 3: Edit `.env` File

Open `.env` in your favorite text editor and add your API keys:

```bash
# Using VS Code
code .env

# Using Vim
vim .env

# Using Nano
nano .env
```

**Edit the file to add your keys**:
```env
# Replace the placeholder values with your actual API keys
NEBIUS_API_KEY=sk-your-actual-nebius-key-here
OPENROUTER_API_KEY=sk-or-your-actual-openrouter-key-here
GEMINI_API_KEY=AIzaYourActualGeminiKeyHere

# Keep these defaults
DATABASE_URL=sqlite:///./data/ocr_platform.db
MAX_FILE_SIZE=10485760
```

**⚠️ Important**:
- At least ONE API key must be provided
- Keep the other placeholders if you don't have those keys
- Never commit `.env` to git (it's already in `.gitignore`)

### Step 4: Build and Start

```bash
# Build the Docker image and start the container
docker compose up --build
```

**What happens**:
1. Docker downloads base images (Python 3.11, Node 20)
2. Installs `uv` for fast Python package management
3. Installs Python dependencies using `uv` (~15 packages) - **much faster!**
4. Installs Node dependencies and builds frontend with optimizations
5. **Automatically initializes SQLite database** (new!)
6. Starts FastAPI server on port 8000
7. Serves frontend at http://localhost:8000
8. **Enables health monitoring** (new!)

**Expected output**:
```
[+] Building 35.2s (19/19) FINISHED
[+] Running 1/1
 ✔ Container ocr_platform  Started
INFO:     Database initialized at data/ocr_platform.db
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Access the Application

Open your browser and navigate to:
- **Application**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Step 6: Stop the Application

When you're done:
```bash
# Stop containers
docker compose down

# Stop and remove volumes (deletes database)
docker compose down -v
```

---

## Local Development Setup

For developers who want to modify the code or run services separately.

### Backend Setup

#### Step 1: Install Python Dependencies

```bash
cd backend

# Install uv (recommended - much faster!)
# Mac/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install dependencies with uv
uv sync

# OR use pip (slower, traditional method)
# python3 -m venv venv
# source venv/bin/activate  # Mac/Linux
# pip install -r requirements.txt
```

**Expected output**:
```
Resolved 33 packages in 0.5ms
Installed 32 packages in 2s
```

#### Step 2: Initialize Database

```bash
# Run database migrations (using uv)
uv run python -m database.migrations

# OR if using pip/venv:
# python -m database.migrations
```

**Expected output**:
```
✅ Database initialized at: sqlite:///./data/ocr_platform.db
✅ Created tables: schemas, processing_jobs
✅ Inserted 4 template schemas
```

#### Step 3: Configure Environment

Create `.env` file in the project root (same as Docker setup above).

```bash
# From project root
cp .env.example .env
# Edit .env with your API keys
```

#### Step 4: Start Backend Server

```bash
# From backend directory (using uv)
uv run uvicorn main:app --reload --port 8000

# OR if using pip/venv:
# uvicorn main:app --reload --port 8000
```

**Expected output**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Backend is now running at: http://localhost:8000

### Frontend Setup

#### Step 1: Install Node Dependencies

Open a **new terminal** (keep backend running):

```bash
cd frontend

# Install dependencies
npm install
```

**Expected output**:
```
added 142 packages in 3s
```

#### Step 2: Start Development Server

```bash
npm run dev
```

**Expected output**:
```
  VITE v5.3.1  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

Frontend is now running at: http://localhost:5173

#### Step 3: Configure API Proxy (Optional)

If you want the frontend to proxy API requests to the backend:

Edit `frontend/vite.config.ts`:
```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## Configuration

### Environment Variables

All configuration is done via `.env` file in the project root.

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NEBIUS_API_KEY` | Nebius API key | No* | - |
| `OPENROUTER_API_KEY` | OpenRouter API key | No* | - |
| `GEMINI_API_KEY` | Google Gemini API key | No* | - |
| `DATABASE_URL` | SQLite database path | No | `sqlite:///./data/ocr_platform.db` |
| `MAX_FILE_SIZE` | Max upload size in bytes | No | `10485760` (10MB) |

*At least one provider API key is required.

### Provider-Specific Setup

#### Nebius Setup
```env
NEBIUS_API_KEY=sk-your-nebius-key

# No additional configuration needed
# Default model: meta-llama/Meta-Llama-3.1-405B-Instruct
```

#### OpenRouter Setup
```env
OPENROUTER_API_KEY=sk-or-your-openrouter-key

# Available models (auto-detected):
# - anthropic/claude-3.5-sonnet
# - openai/gpt-4o-2024-08-06
# - google/gemini-pro-1.5
# - meta-llama/llama-3.1-405b-instruct
```

#### Gemini Setup
```env
GEMINI_API_KEY=AIzaYourGeminiKey

# Available models (auto-detected):
# - gemini-1.5-pro
# - gemini-1.5-flash
```

### Database Location

The SQLite database is stored in the `data/` directory by default:
```
ocr_platform_testdrive/
└── data/
    └── ocr_platform.db
```

**To change database location**:
```env
# Absolute path
DATABASE_URL=sqlite:////absolute/path/to/database.db

# Relative path
DATABASE_URL=sqlite:///./custom/path/database.db
```

---

## Verification

After setup, verify everything is working correctly.

### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

### 2. Check API Docs

Visit http://localhost:8000/docs in your browser. You should see:
- FastAPI Swagger UI
- List of all endpoints
- Ability to test API endpoints interactively

### 3. Check Frontend

Visit http://localhost:8000 (Docker) or http://localhost:5173 (local dev). You should see:
- **Process** page with file upload
- **History** page with job list
- Navigation between pages

### 4. Test Document Upload

1. Navigate to **Process** page
2. Drag and drop an image (JPG, PNG) or PDF
3. Select a provider (based on your API keys)
4. Select a schema template (e.g., "Invoice")
5. Click "Process Document"
6. Wait for processing to complete
7. View extracted structured data

### 5. Check Database

```bash
# If using Docker
docker compose exec app ls -lh data/

# If running locally
ls -lh data/

# Should show:
# ocr_platform.db - SQLite database file
```

---

## Troubleshooting

### Docker Issues

#### "docker: command not found"
**Solution**: Install Docker Desktop from https://www.docker.com/products/docker-desktop/

#### "Cannot connect to the Docker daemon"
**Solution**: Start Docker Desktop application
- **Mac**: Open Applications → Docker
- **Windows**: Start Docker Desktop from Start Menu

#### Port 8000 Already in Use
**Error**: `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution 1**: Stop the conflicting service
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Solution 2**: Change port in `docker-compose.yml`:
```yaml
services:
  app:
    ports:
      - "8001:8000"  # Use localhost:8001 instead
```

#### Container Won't Start
**Solution**: Check logs
```bash
docker compose logs -f
```

Common issues:
- Missing `.env` file
- Invalid API keys
- Database permission issues

### Backend Issues

#### Module Not Found
**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Mac/Linux
# venv\Scripts\activate   # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database Not Initialized
**Error**: `sqlite3.OperationalError: no such table: schemas`

**Solution**:
```bash
cd backend
python -m database.migrations
```

#### API Key Not Found
**Error**: `API key not configured for provider: nebius`

**Solution**: Add the missing API key to `.env`:
```env
NEBIUS_API_KEY=your-actual-key
```

### Frontend Issues

#### Port 5173 Already in Use
**Error**: `Port 5173 is in use, trying another one...`

**Solution 1**: Stop the conflicting Vite process
```bash
lsof -i :5173
kill -9 <PID>
```

**Solution 2**: Let Vite use a different port (it will auto-increment to 5174)

#### Module Not Found (Node)
**Error**: `Cannot find module 'react'`

**Solution**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### API Connection Refused
**Error**: `ERR_CONNECTION_REFUSED` when calling API

**Solution**: Ensure backend is running
```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start it
cd backend
uvicorn main:app --reload --port 8000
```

### VLM Provider Issues

#### Invalid API Key
**Error**: `401 Unauthorized` or `Invalid API key`

**Solution**:
1. Verify API key is correct
2. Check for extra spaces or quotes in `.env`
3. Regenerate API key from provider dashboard
4. Restart application after updating `.env`

#### Rate Limit Exceeded
**Error**: `429 Too Many Requests`

**Solution**:
- Wait a few minutes before retrying
- Check provider rate limits:
  - Nebius: Varies by plan
  - OpenRouter: Varies by model
  - Gemini: 15 requests/minute (free tier)

#### Model Not Available
**Error**: `Model not found: xyz`

**Solution**:
- Check provider docs for available models
- Use `/api/providers` endpoint to see available models
- Update model selection in frontend

### Database Issues

#### Database Locked
**Error**: `sqlite3.OperationalError: database is locked`

**Solution**:
```bash
# Stop all applications accessing the database
docker compose down

# Remove lock file
rm data/ocr_platform.db-shm
rm data/ocr_platform.db-wal

# Restart
docker compose up
```

#### Corrupted Database
**Error**: `sqlite3.DatabaseError: database disk image is malformed`

**Solution**:
```bash
# Backup (if possible)
cp data/ocr_platform.db data/ocr_platform.db.backup

# Reinitialize database
rm data/ocr_platform.db
docker compose up  # Will auto-initialize
```

---

## Next Steps

After successful setup:

1. **Read the User Guide**: `docs/USER_GUIDE.md`
2. **Try the Examples**: Test with sample documents
3. **Create Custom Schemas**: See `SCHEMA_GUIDE.md`
4. **Explore the API**: Visit http://localhost:8000/docs
5. **Run Tests**: See `docs/TESTING_GUIDE.md`

---

## Additional Resources

- **Main Documentation**: `README.md`
- **Schema Guide**: `SCHEMA_GUIDE.md`
- **Testing Guide**: `docs/TESTING_GUIDE.md` (to be created)
- **API Documentation**: http://localhost:8000/docs (when running)
- **Design Document**: `docs/plan.md`

---

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Check `docs/TROUBLESHOOTING.md` (to be created)
3. Review logs: `docker compose logs -f`
4. Open an issue on GitHub (if applicable)

---

**Last Updated**: 2026-01-16
**Version**: 1.0.0
**Status**: Production Ready
