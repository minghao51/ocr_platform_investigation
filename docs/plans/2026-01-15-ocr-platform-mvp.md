# OCR Platform MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a dockerized OCR platform that allows users to upload images/PDFs, process them with configurable VLM providers (Nebius, OpenRouter, Gemini), extract structured data using Pydantic schemas, and view/export historical processing results.

**Architecture:** FastAPI backend with SQLite database, React frontend with TypeScript, multi-stage Docker build, provider abstraction layer for VLM integration, and Pydantic-based schema validation system.

**Tech Stack:**
- Backend: FastAPI, Python 3.11+, aiosqlite, Pydantic v2, pdf2image, httpx
- Frontend: React 18, TypeScript, Vite, TailwindCSS, CodeMirror, React Table
- Infrastructure: Docker, Docker Compose, SQLite
- VLM Providers: Nebius, OpenRouter, Google Gemini

---

## Phase 1: Foundation (Project Structure & Docker)

### Task 1: Create Monorepo Directory Structure

**Files:**
- Create: `backend/`
- Create: `frontend/`
- Create: `data/`
- Create: `docs/plans/`

**Step 1: Create all top-level directories**

Run:
```bash
cd /Users/minghao/Desktop/personal/ocr_platform_testdrive
mkdir -p backend frontend data docs/plans
```

Expected: Directories created

**Step 2: Create .gitignore**

Run:
```bash
cat > .gitignore << 'EOF'
# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
*.egg-info/
dist/
build/

# Data
data/
*.db
*.db-journal

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Docker
.dockerignore

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
EOF
```

Expected: .gitignore created

**Step 3: Initialize git repository**

Run:
```bash
git init
git add .gitignore
git commit -m "chore: initialize git repository with gitignore"
```

Expected: Git repository initialized, initial commit created

---

### Task 2: Setup Backend Project Structure

**Files:**
- Create: `backend/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/database/__init__.py`
- Create: `backend/database/schema.sql`
- Create: `backend/database/migrations.py`
- Create: `backend/database/crud.py`
- Create: `backend/models/__init__.py`
- Create: `backend/models/schemas.py`
- Create: `backend/models/providers.py`
- Create: `backend/services/__init__.py`
- Create: `backend/services/vlm_provider.py`
- Create: `backend/services/nebius.py`
- Create: `backend/services/openrouter.py`
- Create: `backend/services/gemini.py`
- Create: `backend/services/schema_service.py`
- Create: `backend/services/image_service.py`
- Create: `backend/services/processing.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/routers/upload.py`
- Create: `backend/routers/processing.py`
- Create: `backend/routers/schemas.py`
- Create: `backend/routers/jobs.py`
- Create: `backend/routers/providers.py`

**Step 1: Create all backend directories**

Run:
```bash
cd backend
mkdir -p database models services routers
```

Expected: Directories created

**Step 2: Create all __init__.py files**

Run:
```bash
touch database/__init__.py models/__init__.py services/__init__.py routers/__init__.py
```

Expected: __init__.py files created in all packages

**Step 3: Create minimal main.py**

Write:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 4: Create requirements.txt**

Write:
```txt
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.10.0
pydantic-settings==2.6.0
httpx==0.28.0
aiosqlite==0.20.0
python-multipart==0.0.12
python-dotenv==1.0.1
pdf2image==1.17.0
pillow==11.0.0
```

**Step 5: Create minimal config.py**

Write:
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    nebius_api_key: str = ""
    openrouter_api_key: str = ""
    gemini_api_key: str = ""

    database_url: str = "sqlite:///./data/ocr_platform.db"

    max_file_size: int = 10 * 1024 * 1024  # 10MB

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()
```

**Step 6: Commit**

Run:
```bash
git add backend/
git commit -m "feat: setup backend project structure and dependencies"
```

Expected: Commit created with backend structure

---

### Task 3: Setup Frontend Project with Vite

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/styles/globals.css`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`

**Step 1: Create package.json**

Write:
```json
{
  "name": "ocr-platform-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "axios": "^1.7.7",
    "react-dropzone": "^14.2.3",
    "@uiw/react-codemirror": "^4.23.5",
    "@codemirror/lang-json": "^6.0.1",
    "@tanstack/react-table": "^8.20.1",
    "lucide-react": "^0.454.0",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.15",
    "typescript": "^5.6.3",
    "vite": "^5.4.11"
  }
}
```

**Step 2: Create vite.config.ts**

Write:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://backend:8000',
        changeOrigin: true,
      }
    }
  }
})
```

**Step 3: Create tsconfig.json**

Write:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

**Step 4: Create tsconfig.node.json**

Write:
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

**Step 5: Create index.html**

Write:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>OCR Platform</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**Step 6: Create main.tsx**

Write:
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './styles/globals.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

**Step 7: Create App.tsx**

Write:
```typescript
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <h1 className="text-3xl font-bold text-center py-8">OCR Platform</h1>
    </div>
  )
}

export default App
```

**Step 8: Create src/styles/globals.css**

Write:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

**Step 9: Create tailwind.config.js**

Write:
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Step 10: Create postcss.config.js**

Write:
```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

**Step 11: Commit**

Run:
```bash
git add frontend/
git commit -m "feat: setup frontend project with Vite, React, TypeScript, and Tailwind"
```

Expected: Commit created with frontend structure

---

### Task 4: Create Docker Configuration

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`
- Create: `.env.example`

**Step 1: Create multi-stage Dockerfile**

Write:
```dockerfile
# Stage 1: Backend
FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Stage 2: Frontend
FROM node:20-alpine AS frontend

WORKDIR /app

# Copy frontend package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy frontend code and build
COPY frontend/ .
RUN npm run build

# Stage 3: Final
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy backend from stage 1
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /app /app

# Copy frontend build from stage 2
COPY --from=frontend /app/dist /app/frontend/dist

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Step 2: Create docker-compose.yml**

Write:
```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: ocr_platform
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./backend:/app/backend
    env_file:
      - .env
    restart: unless-stopped
```

**Step 3: Create .dockerignore**

Write:
```gitignore
node_modules
__pycache__
*.pyc
*.pyo
*.pyd
.git
.gitignore
.env
data/
*.db
docs/
.vscode/
.idea/
```

**Step 4: Create .env.example**

Write:
```env
# VLM Provider API Keys
NEBIUS_API_KEY=your_nebius_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=sqlite:///./data/ocr_platform.db

# File Upload
MAX_FILE_SIZE=10485760
```

**Step 5: Commit**

Run:
```bash
git add Dockerfile docker-compose.yml .dockerignore .env.example
git commit -m "feat: add Docker configuration with multi-stage build"
```

Expected: Commit created with Docker setup

---

### Task 5: Setup Database Schema and Migrations

**Files:**
- Modify: `backend/database/schema.sql`
- Modify: `backend/database/migrations.py`

**Step 1: Write database schema**

Write to `backend/database/schema.sql`:
```sql
-- Schemas table
CREATE TABLE IF NOT EXISTS schemas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    definition TEXT NOT NULL,  -- JSON string of Pydantic model definition
    is_template BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,  -- 'image' or 'pdf'
    provider TEXT NOT NULL,    -- 'nebius', 'openrouter', 'gemini'
    model TEXT NOT NULL,
    schema_id INTEGER,
    schema_name TEXT,
    status TEXT NOT NULL,      -- 'pending', 'processing', 'success', 'error'
    result TEXT,               -- JSON string of extracted data
    error_message TEXT,
    processing_time_seconds REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (schema_id) REFERENCES schemas(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_provider ON processing_jobs(provider);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON processing_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_schemas_is_template ON schemas(is_template);
```

**Step 2: Write migration script**

Write to `backend/database/migrations.py`:
```python
import aiosqlite
import asyncio
from pathlib import Path

DB_PATH = Path("./data/ocr_platform.db")

async def init_database():
    """Initialize database with schema"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        # Read and execute schema
        with open("database/schema.sql", "r") as f:
            schema = f.read()

        await db.executescript(schema)
        await db.commit()

        print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    asyncio.run(init_database())
```

**Step 3: Commit**

Run:
```bash
git add backend/database/
git commit -m "feat: setup database schema and migration script"
```

Expected: Commit created with database schema

---

### Task 6: Create CRUD Operations

**Files:**
- Modify: `backend/database/crud.py`

**Step 1: Write CRUD operations**

Write to `backend/database/crud.py`:
```python
import aiosqlite
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path("./data/ocr_platform.db")

async def create_schema(
    name: str,
    definition: Dict[str, Any],
    description: Optional[str] = None,
    is_template: bool = False
) -> int:
    """Create a new schema"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO schemas (name, description, definition, is_template)
               VALUES (?, ?, ?, ?)""",
            (name, description, json.dumps(definition), is_template)
        )
        await db.commit()
        return cursor.lastrowid

async def get_schema(schema_id: int) -> Optional[Dict[str, Any]]:
    """Get schema by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM schemas WHERE id = ?",
            (schema_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

async def list_schemas(
    is_template: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """List all schemas"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if is_template is not None:
            cursor = await db.execute(
                "SELECT * FROM schemas WHERE is_template = ? ORDER BY name",
                (is_template,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM schemas ORDER BY name"
            )

        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def create_job(
    file_name: str,
    file_type: str,
    provider: str,
    model: str,
    schema_id: Optional[int],
    schema_name: Optional[str]
) -> int:
    """Create a new processing job"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO processing_jobs
               (file_name, file_type, provider, model, schema_id, schema_name, status)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (file_name, file_type, provider, model, schema_id, schema_name, "pending")
        )
        await db.commit()
        return cursor.lastrowid

async def update_job_status(
    job_id: int,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None
) -> None:
    """Update job status"""
    async with aiosqlite.connect(DB_PATH) as db:
        if status == "success":
            completed_at = datetime.now().isoformat()
            await db.execute(
                """UPDATE processing_jobs
                   SET status = ?, result = ?, completed_at = ?, processing_time_seconds = ?
                   WHERE id = ?""",
                (status, json.dumps(result) if result else None, completed_at, processing_time, job_id)
            )
        elif status == "error":
            completed_at = datetime.now().isoformat()
            await db.execute(
                """UPDATE processing_jobs
                   SET status = ?, error_message = ?, completed_at = ?
                   WHERE id = ?""",
                (status, error_message, completed_at, job_id)
            )
        else:
            await db.execute(
                "UPDATE processing_jobs SET status = ? WHERE id = ?",
                (status, job_id)
            )
        await db.commit()

async def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM processing_jobs WHERE id = ?",
            (job_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None

async def list_jobs(
    status: Optional[str] = None,
    provider: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """List jobs with optional filters"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        query = "SELECT * FROM processing_jobs WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

async def delete_job(job_id: int) -> bool:
    """Delete a job"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM processing_jobs WHERE id = ?", (job_id,))
        await db.commit()
        return True
```

**Step 2: Commit**

Run:
```bash
git add backend/database/crud.py
git commit -m "feat: implement CRUD operations for schemas and jobs"
```

Expected: Commit created with CRUD operations

---

### Task 7: Create File Upload Endpoint

**Files:**
- Modify: `backend/routers/upload.py`
- Modify: `backend/main.py`

**Step 1: Write upload router**

Write to `backend/routers/upload.py`:
```python
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing"""

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max size is 10MB")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine file type
    file_type = "pdf" if file_ext == ".pdf" else "image"

    return JSONResponse({
        "file_id": file_id,
        "file_name": file.filename,
        "file_type": file_type,
        "file_path": str(file_path),
        "file_size": len(content)
    })
```

**Step 2: Register upload router in main.py**

Edit `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 3: Commit**

Run:
```bash
git add backend/routers/upload.py backend/main.py
git commit -m "feat: add file upload endpoint with validation"
```

Expected: Commit created with upload functionality

---

## Phase 2: Core Services (VLM Integration)

### Task 8: Create VLM Provider Base Class

**Files:**
- Modify: `backend/services/vlm_provider.py`

**Step 1: Write base provider class**

Write to `backend/services/vlm_provider.py`:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import httpx
import base64
from io import BytesIO
from PIL import Image

class VLMProvider(ABC):
    """Base class for VLM providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    @abstractmethod
    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Process an image and extract structured data"""
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available models"""
        pass

    @abstractmethod
    def get_default_image_size(self) -> tuple[int, int]:
        """Get default image size for this provider"""
        pass

    def encode_image(self, image: Image.Image, format: str = "JPEG") -> str:
        """Encode image to base64"""
        buffer = BytesIO()
        image.save(buffer, format=format)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
```

**Step 2: Commit**

Run:
```bash
git add backend/services/vlm_provider.py
git commit -m "feat: create VLM provider base class"
```

Expected: Commit created

---

### Task 9: Implement Nebius Provider

**Files:**
- Modify: `backend/services/nebius.py`

**Step 1: Write Nebius provider**

Write to `backend/services/nebius.py`:
```python
from typing import Dict, Any, List
from PIL import Image
import json
from .vlm_provider import VLMProvider

class NebiusProvider(VLMProvider):
    """Nebius AI Studio provider"""

    BASE_URL = "https://api.studio.nebius.ai/v1"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "meta-llama/Llama-3.2-90B-Vision-Instruct",
        **kwargs
    ) -> Dict[str, Any]:
        """Process image with Nebius"""

        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.encode_image(image)}"
                        }
                    }
                ]
            }
        ]

        # Make API call
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 4096)
            }
        )

        response.raise_for_status()
        result = response.json()

        # Extract content
        content = result["choices"][0]["message"]["content"]

        return {
            "raw_response": result,
            "content": content,
            "usage": result.get("usage", {})
        }

    def get_models(self) -> List[str]:
        return [
            "meta-llama/Llama-3.2-90B-Vision-Instruct",
            "meta-llama/Llama-3.2-11B-Vision-Instruct"
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
```

**Step 2: Commit**

Run:
```bash
git add backend/services/nebius.py
git commit -m "feat: implement Nebius VLM provider"
```

Expected: Commit created

---

### Task 10: Implement OpenRouter Provider

**Files:**
- Modify: `backend/services/openrouter.py`

**Step 1: Write OpenRouter provider**

Write to `backend/services/openrouter.py`:
```python
from typing import Dict, Any, List
from PIL import Image
import json
from .vlm_provider import VLMProvider

class OpenRouterProvider(VLMProvider):
    """OpenRouter provider"""

    BASE_URL = "https://openrouter.ai/api/v1"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "anthropic/claude-3.5-sonnet",
        **kwargs
    ) -> Dict[str, Any]:
        """Process image with OpenRouter"""

        # Prepare messages
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{self.encode_image(image)}"
                        }
                    }
                ]
            }
        ]

        # Make API call
        response = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 4096)
            }
        )

        response.raise_for_status()
        result = response.json()

        # Extract content
        content = result["choices"][0]["message"]["content"]

        return {
            "raw_response": result,
            "content": content,
            "usage": result.get("usage", {})
        }

    def get_models(self) -> List[str]:
        return [
            "anthropic/claude-3.5-sonnet",
            "google/gemini-pro-1.5",
            "openai/gpt-4o",
            "meta-llama/llama-3.2-90b-vision-preview"
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
```

**Step 2: Commit**

Run:
```bash
git add backend/services/openrouter.py
git commit -m "feat: implement OpenRouter VLM provider"
```

Expected: Commit created

---

### Task 11: Implement Gemini Provider

**Files:**
- Modify: `backend/services/gemini.py`

**Step 1: Write Gemini provider**

Write to `backend/services/gemini.py`:
```python
from typing import Dict, Any, List
from PIL import Image
import json
from .vlm_provider import VLMProvider

class GeminiProvider(VLMProvider):
    """Google Gemini provider"""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    async def process_image(
        self,
        image: Image.Image,
        prompt: str,
        schema: Dict[str, Any],
        model: str = "gemini-1.5-pro",
        **kwargs
    ) -> Dict[str, Any]:
        """Process image with Gemini"""

        # Prepare content
        content = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{prompt}\n\nRespond ONLY with valid JSON matching this schema:\n{json.dumps(schema, indent=2)}"
                        },
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": self.encode_image(image)
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": kwargs.get("temperature", 0.1),
                "maxOutputTokens": kwargs.get("max_tokens", 4096),
                "responseMimeType": "application/json"
            }
        }

        # Make API call
        response = await self.client.post(
            f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}",
            headers={"Content-Type": "application/json"},
            json=content
        )

        response.raise_for_status()
        result = response.json()

        # Extract content
        content_text = result["candidates"][0]["content"]["parts"][0]["text"]

        return {
            "raw_response": result,
            "content": content_text,
            "usage": result.get("usageMetadata", {})
        }

    def get_models(self) -> List[str]:
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]

    def get_default_image_size(self) -> tuple[int, int]:
        return (1024, 1024)
```

**Step 2: Commit**

Run:
```bash
git add backend/services/gemini.py
git commit -m "feat: implement Gemini VLM provider"
```

Expected: Commit created

---

### Task 12: Implement Image Processing Service

**Files:**
- Modify: `backend/services/image_service.py`

**Step 1: Write image service**

Write to `backend/services/image_service.py`:
```python
from pathlib import Path
from typing import List
from PIL import Image
import pdf2image
from io import BytesIO

class ImageService:
    """Service for processing images and PDFs"""

    @staticmethod
    def load_image(file_path: str) -> Image.Image:
        """Load an image file"""
        return Image.open(file_path)

    @staticmethod
    def resize_image(
        image: Image.Image,
        target_size: tuple[int, int],
        maintain_aspect: bool = True
    ) -> Image.Image:
        """Resize image to target size"""

        if maintain_aspect:
            # Calculate aspect ratio
            aspect_ratio = image.width / image.height
            target_width, target_height = target_size

            if aspect_ratio > target_width / target_height:
                # Width is limiting factor
                new_width = target_width
                new_height = int(target_width / aspect_ratio)
            else:
                # Height is limiting factor
                new_height = target_height
                new_width = int(target_height * aspect_ratio)

            return image.resize((new_width, new_height), Image.LANCZOS)
        else:
            return image.resize(target_size, Image.LANCZOS)

    @staticmethod
    def pdf_to_images(
        pdf_path: str,
        dpi: int = 200,
        first_page: int = None,
        last_page: int = None
    ) -> List[Image.Image]:
        """Convert PDF to list of images"""

        images = pdf2image.convert_from_path(
            pdf_path,
            dpi=dpi,
            first_page=first_page,
            last_page=last_page
        )

        return images

    @staticmethod
    def optimize_image(image: Image.Image, max_size: int = 5 * 1024 * 1024) -> bytes:
        """Optimize image to stay under size limit"""

        # Try different quality levels
        for quality in [95, 85, 75, 65, 55]:
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=quality, optimize=True)
            size = buffer.tell()

            if size <= max_size:
                return buffer.getvalue()

        # If still too large, resize
        width, height = image.size
        scale = 0.9
        while scale > 0.1:
            new_size = (int(width * scale), int(height * scale))
            resized = image.resize(new_size, Image.LANCZOS)

            for quality in [85, 75, 65]:
                buffer = BytesIO()
                resized.save(buffer, format="JPEG", quality=quality, optimize=True)
                if buffer.tell() <= max_size:
                    return buffer.getvalue()

            scale -= 0.1

        raise ValueError("Unable to optimize image to target size")
```

**Step 2: Commit**

Run:
```bash
git add backend/services/image_service.py
git commit -m "feat: implement image processing service"
```

Expected: Commit created

---

### Task 13: Implement Schema Validation Service

**Files:**
- Modify: `backend/services/schema_service.py`

**Step 1: Write schema validation service**

Write to `backend/services/schema_service.py`:
```python
from typing import Dict, Any, Type
from pydantic import BaseModel, ValidationError
import json

class SchemaService:
    """Service for validating and managing Pydantic schemas"""

    @staticmethod
    def create_pydantic_model(schema_definition: Dict[str, Any]) -> Type[BaseModel]:
        """Create a Pydantic model from a schema definition"""

        # Use TypeAdapter for complex nested schemas
        from pydantic import TypeAdapter

        try:
            # Create a TypeAdapter from the schema
            adapter = TypeAdapter(schema_definition)
            return adapter
        except Exception as e:
            raise ValueError(f"Invalid schema definition: {str(e)}")

    @staticmethod
    def validate_data(
        data: Dict[str, Any],
        schema_definition: Dict[str, Any]
    ) -> tuple[bool, Any, str]:
        """Validate data against schema"""

        try:
            adapter = SchemaService.create_pydantic_model(schema_definition)
            validated_data = adapter.validate_python(data)
            return True, validated_data, None
        except ValidationError as e:
            error_msg = SchemaService.format_validation_error(e)
            return False, None, error_msg
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def format_validation_error(error: ValidationError) -> str:
        """Format Pydantic validation error"""

        errors = []
        for err in error.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            errors.append(f"{loc}: {err['msg']}")

        return "\n".join(errors)

    @staticmethod
    def get_builtin_templates() -> Dict[str, Dict[str, Any]]:
        """Get built-in schema templates"""

        return {
            "Invoice": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string"},
                    "date": {"type": "string"},
                    "vendor": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                                "total": {"type": "number"}
                            },
                            "required": ["description", "quantity", "unit_price", "total"]
                        }
                    },
                    "subtotal": {"type": "number"},
                    "tax": {"type": "number"},
                    "total": {"type": "number"}
                },
                "required": ["invoice_number", "date", "vendor", "items", "total"]
            },
            "Receipt": {
                "type": "object",
                "properties": {
                    "merchant": {"type": "string"},
                    "date": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "number"}
                            },
                            "required": ["name", "price"]
                        }
                    },
                    "total": {"type": "number"},
                    "payment_method": {"type": "string"}
                },
                "required": ["merchant", "date", "items", "total"]
            },
            "ID": {
                "type": "object",
                "properties": {
                    "document_type": {"type": "string"},
                    "full_name": {"type": "string"},
                    "date_of_birth": {"type": "string"},
                    "document_number": {"type": "string"},
                    "expiration_date": {"type": "string"},
                    "address": {"type": "string"}
                },
                "required": ["document_type", "full_name", "document_number"]
            },
            "Generic": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
```

**Step 2: Commit**

Run:
```bash
git add backend/services/schema_service.py
git commit -m "feat: implement schema validation service with built-in templates"
```

Expected: Commit created

---

### Task 14: Implement Main Processing Pipeline

**Files:**
- Modify: `backend/services/processing.py`
- Modify: `backend/models/schemas.py`

**Step 1: Create Pydantic models**

Write to `backend/models/schemas.py`:
```python
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ProcessRequest(BaseModel):
    file_id: str
    provider: str  # 'nebius', 'openrouter', 'gemini'
    model: str
    schema_id: Optional[int] = None
    schema_definition: Optional[Dict[str, Any]] = None
    prompt: Optional[str] = "Extract all information from this document"
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 4096

class ProcessResponse(BaseModel):
    job_id: int
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
```

**Step 2: Write processing pipeline**

Write to `backend/services/processing.py`:
```python
import time
from pathlib import Path
from typing import Dict, Any, Optional
from config import get_settings
from services.nebius import NebiusProvider
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider
from services.image_service import ImageService
from services.schema_service import SchemaService
from database import crud

settings = get_settings()

class ProcessingService:
    """Main processing pipeline"""

    def __init__(self):
        self.providers = {
            "nebius": NebiusProvider,
            "openrouter": OpenRouterProvider,
            "gemini": GeminiProvider
        }
        self.image_service = ImageService()
        self.schema_service = SchemaService()

    def get_provider(self, provider_name: str, api_key: str):
        """Get provider instance"""
        provider_class = self.providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown provider: {provider_name}")

        return provider_class(api_key)

    async def process_file(
        self,
        file_id: str,
        file_path: str,
        file_type: str,
        provider_name: str,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a file (image or PDF)"""

        # Get API key
        api_key = getattr(settings, f"{provider_name}_api_key")
        if not api_key:
            raise ValueError(f"No API key configured for {provider_name}")

        async with self.get_provider(provider_name, api_key) as provider:
            if file_type == "image":
                return await self._process_single_image(
                    file_path, provider, model, schema_definition, prompt, **kwargs
                )
            else:  # PDF
                return await self._process_pdf(
                    file_path, provider, model, schema_definition, prompt, **kwargs
                )

    async def _process_single_image(
        self,
        image_path: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process a single image"""

        # Load image
        image = self.image_service.load_image(image_path)

        # Resize for provider
        target_size = provider.get_default_image_size()
        image = self.image_service.resize_image(image, target_size)

        # Process with VLM
        result = await provider.process_image(image, prompt, schema_definition, model, **kwargs)

        # Validate result
        content = result.get("content", "{}")

        try:
            import json
            data = json.loads(content)
            is_valid, validated_data, error = self.schema_service.validate_data(
                data, schema_definition
            )

            if is_valid:
                return {
                    "success": True,
                    "data": validated_data,
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": f"Validation failed: {error}",
                    "raw_response": result
                }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON response: {str(e)}",
                "raw_response": result
            }

    async def _process_pdf(
        self,
        pdf_path: str,
        provider,
        model: str,
        schema_definition: Dict[str, Any],
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Process PDF (multiple pages)"""

        # Convert PDF to images
        images = self.image_service.pdf_to_images(pdf_path)

        results = []
        errors = []

        for i, image in enumerate(images):
            # Resize
            target_size = provider.get_default_image_size()
            resized = self.image_service.resize_image(image, target_size)

            # Process
            result = await provider.process_image(resized, prompt, schema_definition, model, **kwargs)

            # Validate
            content = result.get("content", "{}")
            try:
                import json
                data = json.loads(content)
                is_valid, validated_data, error = self.schema_service.validate_data(
                    data, schema_definition
                )

                if is_valid:
                    results.append(validated_data)
                else:
                    errors.append(f"Page {i+1}: {error}")
            except json.JSONDecodeError as e:
                errors.append(f"Page {i+1}: Invalid JSON - {str(e)}")

        return {
            "success": len(errors) == 0,
            "data": results,
            "errors": errors if errors else None,
            "total_pages": len(images),
            "successful_pages": len(results)
        }

async def run_processing_job(job_id: int) -> None:
    """Run a processing job (called asynchronously)"""

    from config import get_settings
    from pathlib import Path

    # Get job details
    job = await crud.get_job(job_id)
    if not job:
        return

    # Update status to processing
    await crud.update_job_status(job_id, "processing")

    # Get file path
    file_path = f"./data/uploads/{job['file_id']}"
    file_ext = Path(file_path).suffix

    # Determine file type from job record
    file_type = job['file_type']

    # Get schema
    if job['schema_id']:
        schema_record = await crud.get_schema(job['schema_id'])
        if schema_record:
            import json
            schema_definition = json.loads(schema_record['definition'])
        else:
            schema_definition = SchemaService.get_builtin_templates()["Generic"]
    else:
        schema_definition = SchemaService.get_builtin_templates()["Generic"]

    # Process
    service = ProcessingService()
    start_time = time.time()

    try:
        result = await service.process_file(
            file_id=job['file_id'],
            file_path=file_path,
            file_type=file_type,
            provider_name=job['provider'],
            model=job['model'],
            schema_definition=schema_definition,
            prompt="Extract all information from this document",
            temperature=0.1,
            max_tokens=4096
        )

        processing_time = time.time() - start_time

        if result['success']:
            await crud.update_job_status(
                job_id,
                "success",
                result=result.get('data'),
                processing_time=processing_time
            )
        else:
            await crud.update_job_status(
                job_id,
                "error",
                error_message=result.get('error'),
                processing_time=processing_time
            )

    except Exception as e:
        processing_time = time.time() - start_time
        await crud.update_job_status(
            job_id,
            "error",
            error_message=str(e),
            processing_time=processing_time
        )
```

**Step 3: Commit**

Run:
```bash
git add backend/services/processing.py backend/models/schemas.py
git commit -m "feat: implement main processing pipeline"
```

Expected: Commit created

---

### Task 15: Create Processing Endpoint

**Files:**
- Modify: `backend/routers/processing.py`
- Modify: `backend/main.py`

**Step 1: Write processing router**

Write to `backend/routers/processing.py`:
```python
from fastapi import APIRouter, HTTPException, BackgroundTasks
from models.schemas import ProcessRequest, ProcessResponse
from database import crud
from services.processing import run_processing_job
import json

router = APIRouter(prefix="/api/process", tags=["processing"])

@router.post("/", response_model=ProcessResponse)
async def process_document(request: ProcessRequest, background_tasks: BackgroundTasks):
    """Process a document with VLM"""

    # Get schema definition
    if request.schema_id:
        schema_record = await crud.get_schema(request.schema_id)
        if not schema_record:
            raise HTTPException(status_code=404, detail="Schema not found")

        schema_definition = json.loads(schema_record["definition"])
        schema_name = schema_record["name"]
    elif request.schema_definition:
        schema_definition = request.schema_definition
        schema_name = "Custom"
    else:
        raise HTTPException(
            status_code=400,
            detail="Either schema_id or schema_definition must be provided"
        )

    # Create job record
    # We need to get file info from the file_id
    from pathlib import Path
    file_path = Path(f"./data/uploads/{request.file_id}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine file type
    file_ext = file_path.suffix.lower()
    file_type = "pdf" if file_ext == ".pdf" else "image"

    # Create job
    job_id = await crud.create_job(
        file_name=file_path.name,
        file_type=file_type,
        provider=request.provider,
        model=request.model,
        schema_id=request.schema_id,
        schema_name=schema_name
    )

    # Queue background processing
    background_tasks.add_task(run_processing_job, job_id)

    return ProcessResponse(
        job_id=job_id,
        status="pending"
    )

@router.get("/status/{job_id}")
async def get_job_status(job_id: int):
    """Get processing job status"""

    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job["id"],
        "status": job["status"],
        "result": job.get("result"),
        "error": job.get("error_message"),
        "processing_time": job.get("processing_time_seconds")
    }
```

**Step 2: Register router in main.py**

Edit `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, processing

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(processing.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 3: Commit**

Run:
```bash
git add backend/routers/processing.py backend/main.py
git commit -m "feat: add processing endpoint with background tasks"
```

Expected: Commit created

---

### Task 16: Create Schemas CRUD Endpoint

**Files:**
- Modify: `backend/routers/schemas.py`
- Modify: `backend/main.py`

**Step 1: Write schemas router**

Write to `backend/routers/schemas.py`:
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from database import crud
from services.schema_service import SchemaService
import json

router = APIRouter(prefix="/api/schemas", tags=["schemas"])

class SchemaCreate(BaseModel):
    name: str
    definition: Dict[str, Any]
    description: Optional[str] = None

class SchemaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    definition: Dict[str, Any]
    is_template: bool
    created_at: str
    updated_at: str

@router.get("/")
async def list_schemas(is_template: Optional[bool] = None):
    """List all schemas"""

    schemas = await crud.list_schemas(is_template=is_template)

    return [
        {
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "definition": json.loads(s["definition"]),
            "is_template": bool(s["is_template"]),
            "created_at": s["created_at"],
            "updated_at": s["updated_at"]
        }
        for s in schemas
    ]

@router.post("/")
async def create_schema(schema: SchemaCreate):
    """Create a new schema"""

    try:
        schema_id = await crud.create_schema(
            name=schema.name,
            definition=schema.definition,
            description=schema.description,
            is_template=False
        )

        created = await crud.get_schema(schema_id)
        return {
            "id": created["id"],
            "name": created["name"],
            "description": created["description"],
            "definition": json.loads(created["definition"]),
            "is_template": bool(created["is_template"]),
            "created_at": created["created_at"],
            "updated_at": created["updated_at"]
        }
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Schema name already exists")
        raise

@router.get("/templates")
async def get_templates():
    """Get built-in schema templates"""

    templates = SchemaService.get_builtin_templates()

    return [
        {
            "name": name,
            "definition": definition,
            "is_template": True,
            "description": f"Built-in {name} template"
        }
        for name, definition in templates.items()
    ]

@router.get("/{schema_id}")
async def get_schema(schema_id: int):
    """Get schema by ID"""

    schema = await crud.get_schema(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")

    return {
        "id": schema["id"],
        "name": schema["name"],
        "description": schema["description"],
        "definition": json.loads(schema["definition"]),
        "is_template": bool(schema["is_template"]),
        "created_at": schema["created_at"],
        "updated_at": schema["updated_at"]
    }
```

**Step 2: Register router in main.py**

Edit `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, processing, schemas

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(schemas.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 3: Commit**

Run:
```bash
git add backend/routers/schemas.py backend/main.py
git commit -m "feat: add schemas CRUD endpoint"
```

Expected: Commit created

---

### Task 17: Create Jobs History Endpoint

**Files:**
- Modify: `backend/routers/jobs.py`
- Modify: `backend/main.py`

**Step 1: Write jobs router**

Write to `backend/routers/jobs.py`:
```python
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from database import crud
import json

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/")
async def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    provider: Optional[str] = Query(None, description="Filter by provider"),
    limit: int = Query(100, description="Max results")
):
    """List processing jobs"""

    jobs = await crud.list_jobs(status=status, provider=provider, limit=limit)

    return [
        {
            "id": job["id"],
            "file_name": job["file_name"],
            "file_type": job["file_type"],
            "provider": job["provider"],
            "model": job["model"],
            "schema_name": job["schema_name"],
            "status": job["status"],
            "result": json.loads(job["result"]) if job.get("result") else None,
            "error": job.get("error_message"),
            "processing_time_seconds": job.get("processing_time_seconds"),
            "created_at": job["created_at"],
            "completed_at": job.get("completed_at")
        }
        for job in jobs
    ]

@router.get("/{job_id}")
async def get_job(job_id: int):
    """Get job details"""

    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "id": job["id"],
        "file_name": job["file_name"],
        "file_type": job["file_type"],
        "provider": job["provider"],
        "model": job["model"],
        "schema_id": job.get("schema_id"),
        "schema_name": job["schema_name"],
        "status": job["status"],
        "result": json.loads(job["result"]) if job.get("result") else None,
        "error": job.get("error_message"),
        "processing_time_seconds": job.get("processing_time_seconds"),
        "created_at": job["created_at"],
        "completed_at": job.get("completed_at")
    }

@router.delete("/{job_id}")
async def delete_job(job_id: int):
    """Delete a job"""

    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await crud.delete_job(job_id)

    return {"message": "Job deleted successfully"}
```

**Step 2: Register router in main.py**

Edit `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, processing, schemas, jobs

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(schemas.router)
app.include_router(jobs.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 3: Commit**

Run:
```bash
git add backend/routers/jobs.py backend/main.py
git commit -m "feat: add jobs history endpoint"
```

Expected: Commit created

---

### Task 18: Create Providers Config Endpoint

**Files:**
- Modify: `backend/routers/providers.py`
- Modify: `backend/main.py`

**Step 1: Write providers router**

Write to `backend/routers/providers.py`:
```python
from fastapi import APIRouter
from services.nebius import NebiusProvider
from services.openrouter import OpenRouterProvider
from services.gemini import GeminiProvider

router = APIRouter(prefix="/api/providers", tags=["providers"])

@router.get("/")
async def list_providers():
    """List available VLM providers and their models"""

    providers = {
        "nebius": {
            "name": "Nebius",
            "models": NebiusProvider.get_models(None)
        },
        "openrouter": {
            "name": "OpenRouter",
            "models": OpenRouterProvider.get_models(None)
        },
        "gemini": {
            "name": "Google Gemini",
            "models": GeminiProvider.get_models(None)
        }
    }

    return providers
```

**Step 2: Register router in main.py**

Edit `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, processing, schemas, jobs, providers

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(schemas.router)
app.include_router(jobs.router)
app.include_router(providers.router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 3: Commit**

Run:
```bash
git add backend/routers/providers.py backend/main.py
git commit -m "feat: add providers config endpoint"
```

Expected: Commit created

---

## Phase 3: User Interface (Frontend)

### Task 19: Create API Client Library

**Files:**
- Create: `frontend/src/lib/api.ts`

**Step 1: Write API client**

Write to `frontend/src/lib/api.ts`:
```typescript
import axios from 'axios';

const API_BASE_URL = '/api';

export interface UploadResponse {
  file_id: string;
  file_name: string;
  file_type: 'image' | 'pdf';
  file_path: string;
  file_size: number;
}

export interface Provider {
  name: string;
  models: string[];
}

export interface Providers {
  [key: string]: Provider;
}

export interface Schema {
  id?: number;
  name: string;
  description?: string;
  definition: any;
  is_template: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Job {
  id: number;
  file_name: string;
  file_type: string;
  provider: string;
  model: string;
  schema_name: string;
  status: 'pending' | 'processing' | 'success' | 'error';
  result?: any;
  error?: string;
  processing_time_seconds?: number;
  created_at: string;
  completed_at?: string;
}

export const api = {
  // Upload
  uploadFile: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_BASE_URL}/upload/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    return response.data;
  },

  // Providers
  getProviders: async (): Promise<Providers> => {
    const response = await axios.get(`${API_BASE_URL}/providers/`);
    return response.data;
  },

  // Schemas
  getSchemas: async (isTemplate?: boolean): Promise<Schema[]> => {
    const params = isTemplate !== undefined ? { is_template: isTemplate } : {};
    const response = await axios.get(`${API_BASE_URL}/schemas/`, { params });
    return response.data;
  },

  getTemplates: async (): Promise<Schema[]> => {
    const response = await axios.get(`${API_BASE_URL}/schemas/templates`);
    return response.data;
  },

  getSchema: async (id: number): Promise<Schema> => {
    const response = await axios.get(`${API_BASE_URL}/schemas/${id}`);
    return response.data;
  },

  createSchema: async (schema: Omit<Schema, 'id' | 'is_template' | 'created_at' | 'updated_at'>): Promise<Schema> => {
    const response = await axios.post(`${API_BASE_URL}/schemas/`, schema);
    return response.data;
  },

  // Processing
  processDocument: async (request: {
    file_id: string;
    provider: string;
    model: string;
    schema_id?: number;
    schema_definition?: any;
    prompt?: string;
    temperature?: number;
    max_tokens?: number;
  }): Promise<{ job_id: number; status: string }> => {
    const response = await axios.post(`${API_BASE_URL}/process/`, request);
    return response.data;
  },

  getJobStatus: async (jobId: number): Promise<Job> => {
    const response = await axios.get(`${API_BASE_URL}/process/status/${jobId}`);
    return response.data;
  },

  // Jobs
  getJobs: async (params?: {
    status?: string;
    provider?: string;
    limit?: number;
  }): Promise<Job[]> => {
    const response = await axios.get(`${API_BASE_URL}/jobs/`, { params });
    return response.data;
  },

  getJob: async (jobId: number): Promise<Job> => {
    const response = await axios.get(`${API_BASE_URL}/jobs/${jobId}`);
    return response.data;
  },

  deleteJob: async (jobId: number): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/jobs/${jobId}`);
  },
};
```

**Step 2: Commit**

Run:
```bash
git add frontend/src/lib/api.ts
git commit -m "feat: create API client library"
```

Expected: Commit created

---

### Task 20: Create File Upload Component

**Files:**
- Create: `frontend/src/components/FileUpload.tsx`

**Step 1: Write FileUpload component**

Write to `frontend/src/components/FileUpload.tsx`:
```typescript
import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';

interface FileUploadProps {
  onFileUploaded: (fileData: { file_id: string; file_name: string; file_type: string }) => void;
  disabled?: boolean;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileUploaded, disabled = false }) => {
  const [uploading, setUploading] = React.useState(false);
  const [uploadedFile, setUploadedFile] = React.useState<{ file_id: string; file_name: string } | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload/', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const data = await response.json();
      setUploadedFile({ file_id: data.file_id, file_name: data.file_name });
      onFileUploaded({
        file_id: data.file_id,
        file_name: data.file_name,
        file_type: data.file_type,
      });
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }, [onFileUploaded]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: disabled || uploading,
  });

  const handleClear = () => {
    setUploadedFile(null);
  };

  if (uploadedFile) {
    return (
      <div className="border-2 border-gray-300 rounded-lg p-4 flex items-center justify-between bg-white">
        <div className="flex items-center space-x-3">
          <File className="w-5 h-5 text-gray-600" />
          <span className="text-sm font-medium text-gray-900">{uploadedFile.file_name}</span>
        </div>
        {!disabled && (
          <button
            onClick={handleClear}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        ${disabled || uploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
      {uploading ? (
        <p className="text-gray-600">Uploading...</p>
      ) : (
        <>
          <p className="text-gray-900 font-medium mb-1">
            {isDragActive ? 'Drop file here' : 'Drag & drop file here'}
          </p>
          <p className="text-sm text-gray-500">
            or click to select (JPG, PNG, PDF - Max 10MB)
          </p>
        </>
      )}
    </div>
  );
};
```

**Step 2: Commit**

Run:
```bash
git add frontend/src/components/FileUpload.tsx
git commit -m "feat: create FileUpload component"
```

Expected: Commit created

---

### Task 21: Create Model Selector Component

**Files:**
- Create: `frontend/src/components/ModelSelector.tsx`

**Step 1: Write ModelSelector component**

Write to `frontend/src/components/ModelSelector.tsx`:
```typescript
import React, { useEffect, useState } from 'react';
import { api, Providers } from '../lib/api';

interface ModelSelectorProps {
  provider: string;
  model: string;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
  provider,
  model,
  onProviderChange,
  onModelChange,
}) => {
  const [providers, setProviders] = useState<Providers>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProviders = async () => {
      try {
        const data = await api.getProviders();
        setProviders(data);
      } catch (error) {
        console.error('Failed to load providers:', error);
      } finally {
        setLoading(false);
      }
    };

    loadProviders();
  }, []);

  const selectedProviderModels = providers[provider]?.models || [];

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Provider
        </label>
        <select
          value={provider}
          onChange={(e) => {
            onProviderChange(e.target.value);
            // Reset model when provider changes
            const newProviderModels = providers[e.target.value]?.models || [];
            if (newProviderModels.length > 0) {
              onModelChange(newProviderModels[0]);
            }
          }}
          disabled={loading}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {loading ? (
            <option>Loading providers...</option>
          ) : (
            Object.entries(providers).map(([key, value]) => (
              <option key={key} value={key}>
                {value.name}
              </option>
            ))
          )}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Model
        </label>
        <select
          value={model}
          onChange={(e) => onModelChange(e.target.value)}
          disabled={loading || selectedProviderModels.length === 0}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {selectedProviderModels.length === 0 ? (
            <option>No models available</option>
          ) : (
            selectedProviderModels.map((modelName) => (
              <option key={modelName} value={modelName}>
                {modelName}
              </option>
            ))
          )}
        </select>
      </div>
    </div>
  );
};
```

**Step 2: Commit**

Run:
```bash
git add frontend/src/components/ModelSelector.tsx
git commit -m "feat: create ModelSelector component"
```

Expected: Commit created

---

### Task 22: Create Schema Editor Component

**Files:**
- Create: `frontend/src/components/SchemaEditor.tsx`

**Step 1: Write SchemaEditor component**

Write to `frontend/src/components/SchemaEditor.tsx`:
```typescript
import React, { useEffect, useState, useCallback } from 'react';
import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';
import { api, Schema } from '../lib/api';
import { Save, FileText, CheckCircle, XCircle } from 'lucide-react';

interface SchemaEditorProps {
  schema: string;
  onSchemaChange: (schema: string) => void;
}

export const SchemaEditor: React.FC<SchemaEditorProps> = ({ schema, onSchemaChange }) => {
  const [isValid, setIsValid] = useState(true);
  const [templates, setTemplates] = useState<Schema[]>([]);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveDescription, setSaveDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'success' | 'error'>('idle');

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await api.getTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const validateJson = useCallback((value: string) => {
    try {
      JSON.parse(value);
      setIsValid(true);
    } catch {
      setIsValid(false);
    }
  }, []);

  const handleChange = useCallback((value: string) => {
    onSchemaChange(value);
    validateJson(value);
  }, [onSchemaChange, validateJson]);

  const loadTemplate = async (templateName: string) => {
    try {
      const template = templates.find((t) => t.name === templateName);
      if (template) {
        const formatted = JSON.stringify(template.definition, null, 2);
        onSchemaChange(formatted);
        setIsValid(true);
      }
    } catch (error) {
      console.error('Failed to load template:', error);
    }
  };

  const handleSave = async () => {
    if (!saveName.trim()) {
      alert('Please enter a schema name');
      return;
    }

    if (!isValid) {
      alert('Invalid JSON schema');
      return;
    }

    setSaving(true);
    setSaveStatus('idle');

    try {
      const definition = JSON.parse(schema);
      await api.createSchema({
        name: saveName,
        definition,
        description: saveDescription || undefined,
      });

      setSaveStatus('success');
      setTimeout(() => {
        setShowSaveModal(false);
        setSaveName('');
        setSaveDescription('');
        setSaveStatus('idle');
      }, 1500);
    } catch (error) {
      console.error('Failed to save schema:', error);
      setSaveStatus('error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <FileText className="w-5 h-5 text-gray-600" />
          <h3 className="text-sm font-medium text-gray-700">Schema Definition</h3>
          {isValid ? (
            <CheckCircle className="w-4 h-4 text-green-500" />
          ) : (
            <XCircle className="w-4 h-4 text-red-500" />
          )}
        </div>

        <div className="flex items-center space-x-2">
          <select
            onChange={(e) => {
              if (e.target.value) {
                loadTemplate(e.target.value);
                e.target.value = '';
              }
            }}
            className="text-sm px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Load Template...</option>
            {templates.map((template) => (
              <option key={template.name} value={template.name}>
                {template.name}
              </option>
            ))}
          </select>

          <button
            onClick={() => setShowSaveModal(true)}
            className="flex items-center space-x-1 px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors text-sm"
          >
            <Save className="w-4 h-4" />
            <span>Save</span>
          </button>
        </div>
      </div>

      <div className="flex-1 border border-gray-300 rounded-md overflow-hidden">
        <CodeMirror
          value={schema}
          height="100%"
          extensions={[json()]}
          onChange={handleChange}
          className="text-sm"
        />
      </div>

      {showSaveModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">Save Schema</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="My Schema"
                  disabled={saving}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={saveDescription}
                  onChange={(e) => setSaveDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                  placeholder="Description of this schema..."
                  disabled={saving}
                />
              </div>

              {saveStatus === 'success' && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="w-4 h-4" />
                  <span className="text-sm">Schema saved successfully!</span>
                </div>
              )}

              {saveStatus === 'error' && (
                <div className="flex items-center space-x-2 text-red-600">
                  <XCircle className="w-4 h-4" />
                  <span className="text-sm">Failed to save schema</span>
                </div>
              )}

              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setShowSaveModal(false);
                    setSaveName('');
                    setSaveDescription('');
                    setSaveStatus('idle');
                  }}
                  disabled={saving}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || saveStatus === 'success'}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
```

**Step 2: Commit**

Run:
```bash
git add frontend/src/components/SchemaEditor.tsx
git commit -m "feat: create SchemaEditor component with CodeMirror"
```

Expected: Commit created

---

### Task 23: Create Results Display Component

**Files:**
- Create: `frontend/src/components/ResultsDisplay.tsx`

**Step 1: Write ResultsDisplay component**

Write to `frontend/src/components/ResultsDisplay.tsx`:
```typescript
import React from 'react';
import { CheckCircle, XCircle, AlertCircle, FileText } from 'lucide-react';

interface ResultsDisplayProps {
  status: 'idle' | 'processing' | 'success' | 'error';
  result?: any;
  error?: string;
  processingTime?: number;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  status,
  result,
  error,
  processingTime,
}) => {
  if (status === 'idle') {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <div className="text-center">
          <FileText className="w-16 h-16 mx-auto mb-4" />
          <p>Upload a file and click "Process" to see results</p>
        </div>
      </div>
    );
  }

  if (status === 'processing') {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Processing document...</p>
          <p className="text-sm text-gray-500 mt-2">This may take a moment</p>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="p-6">
        <div className="flex items-center space-x-3 text-red-600 mb-4">
          <XCircle className="w-6 h-6" />
          <h3 className="text-lg font-semibold">Processing Failed</h3>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-sm text-red-800">{error || 'Unknown error'}</p>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="h-full flex flex-col">
        <div className="flex items-center justify-between mb-4 p-4 border-b">
          <div className="flex items-center space-x-3 text-green-600">
            <CheckCircle className="w-6 h-6" />
            <h3 className="text-lg font-semibold">Success</h3>
          </div>

          {processingTime && (
            <div className="text-sm text-gray-500">
              Processing time: {processingTime.toFixed(2)}s
            </div>
          )}
        </div>

        <div className="flex-1 overflow-auto p-4">
          <pre className="text-sm bg-gray-50 p-4 rounded-md overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      </div>
    );
  }

  return null;
};
```

**Step 2: Commit**

Run:
```bash
git add frontend/src/components/ResultsDisplay.tsx
git commit -m "feat: create ResultsDisplay component"
```

Expected: Commit created

---

### Task 24: Create Processing Page

**Files:**
- Create: `frontend/src/pages/ProcessingPage.tsx`

**Step 1: Write ProcessingPage component**

Write to `frontend/src/pages/ProcessingPage.tsx`:
```typescript
import React, { useState } from 'react';
import { FileUpload } from '../components/FileUpload';
import { ModelSelector } from '../components/ModelSelector';
import { SchemaEditor } from '../components/SchemaEditor';
import { ResultsDisplay } from '../components/ResultsDisplay';
import { api } from '../lib/api';
import { Play } from 'lucide-react';

export const ProcessingPage: React.FC = () => {
  const [fileData, setFileData] = useState<{ file_id: string; file_name: string; file_type: string } | null>(null);
  const [provider, setProvider] = useState('nebius');
  const [model, setModel] = useState('');
  const [schema, setSchema] = useState(JSON.stringify({
    type: 'object',
    properties: {
      text: { type: 'string' }
    }
  }, null, 2));
  const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | undefined>();
  const [jobId, setJobId] = useState<number | null>(null);

  const handleProcess = async () => {
    if (!fileData) {
      alert('Please upload a file first');
      return;
    }

    setStatus('processing');
    setResult(null);
    setError(null);

    try {
      const response = await api.processDocument({
        file_id: fileData.file_id,
        provider,
        model,
        schema_definition: JSON.parse(schema),
        prompt: 'Extract all information from this document',
      });

      setJobId(response.job_id);

      // Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const jobStatus = await api.getJobStatus(response.job_id);

          if (jobStatus.status === 'success') {
            setStatus('success');
            setResult(jobStatus.result);
            setProcessingTime(jobStatus.processing_time_seconds);
            clearInterval(pollInterval);
          } else if (jobStatus.status === 'error') {
            setStatus('error');
            setError(jobStatus.error || 'Processing failed');
            setProcessingTime(jobStatus.processing_time_seconds);
            clearInterval(pollInterval);
          }
        } catch (err) {
          console.error('Failed to poll job status:', err);
        }
      }, 1000);
    } catch (err) {
      setStatus('error');
      setError(err instanceof Error ? err.message : 'Processing failed');
    }
  };

  const canProcess = fileData && model && status !== 'processing';

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">OCR Document Processing</h1>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Upload & Config */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">1. Upload File</h2>
              <FileUpload
                onFileUploaded={setFileData}
                disabled={status === 'processing'}
              />
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">2. Configure Model</h2>
              <ModelSelector
                provider={provider}
                model={model}
                onProviderChange={setProvider}
                onModelChange={setModel}
              />
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">3. Define Schema</h2>
              <p className="text-sm text-gray-600 mb-4">
                Define the structure of data you want to extract from the document
              </p>
            </div>
          </div>

          {/* Middle Column: Schema Editor */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow h-full flex flex-col" style={{ minHeight: '600px' }}>
              <div className="p-6 flex-1">
                <SchemaEditor
                  schema={schema}
                  onSchemaChange={setSchema}
                />
              </div>
            </div>
          </div>

          {/* Right Column: Results */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow h-full flex flex-col" style={{ minHeight: '600px' }}>
              <div className="p-6 flex-1 flex flex-col">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Results</h2>
                </div>

                <div className="flex-1">
                  <ResultsDisplay
                    status={status}
                    result={result}
                    error={error}
                    processingTime={processingTime}
                  />
                </div>

                <button
                  onClick={handleProcess}
                  disabled={!canProcess}
                  className={`
                    w-full mt-4 py-3 rounded-md font-medium transition-colors flex items-center justify-center space-x-2
                    ${canProcess
                      ? 'bg-blue-500 text-white hover:bg-blue-600'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }
                  `}
                >
                  <Play className="w-5 h-5" />
                  <span>Process Document</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
```

**Step 2: Commit**

Run:
```bash
git add frontend/src/pages/ProcessingPage.tsx
git commit -m "feat: create ProcessingPage with full layout"
```

Expected: Commit created

---

### Task 25: Create History Page

**Files:**
- Create: `frontend/src/pages/HistoryPage.tsx`

**Step 1: Write HistoryPage component**

Write to `frontend/src/pages/HistoryPage.tsx`:
```typescript
import React, { useEffect, useState } from 'react';
import { api, Job } from '../lib/api';
import { Trash2, FileText, Clock, CheckCircle, XCircle, Loader } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export const HistoryPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'success' | 'error'>('all');

  useEffect(() => {
    loadJobs();
  }, [filter]);

  const loadJobs = async () => {
    setLoading(true);
    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const data = await api.getJobs(params);
      setJobs(data);
    } catch (error) {
      console.error('Failed to load jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (jobId: number) => {
    if (!confirm('Are you sure you want to delete this job?')) return;

    try {
      await api.deleteJob(jobId);
      setJobs(jobs.filter((j) => j.id !== jobId));
    } catch (error) {
      console.error('Failed to delete job:', error);
      alert('Failed to delete job');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'processing':
      case 'pending':
        return <Loader className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Processing History</h1>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-md transition-colors ${
                filter === 'all'
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('success')}
              className={`px-4 py-2 rounded-md transition-colors ${
                filter === 'success'
                  ? 'bg-green-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Success
            </button>
            <button
              onClick={() => setFilter('error')}
              className={`px-4 py-2 rounded-md transition-colors ${
                filter === 'error'
                  ? 'bg-red-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Errors
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Loader className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <FileText className="w-16 h-16 mx-auto mb-4" />
            <p>No jobs found</p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Processing Time
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(job.status)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FileText className="w-5 h-5 text-gray-400 mr-2" />
                        <span className="text-sm font-medium text-gray-900">{job.file_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.provider}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.model}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {job.processing_time_seconds ? `${job.processing_time_seconds.toFixed(2)}s` : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleDelete(job.id)}
                        className="text-red-600 hover:text-red-900 transition-colors"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
```

**Step 2: Commit**

Run:
```bash
git add frontend/src/pages/HistoryPage.tsx
git commit -m "feat: create HistoryPage with filtering"
```

Expected: Commit created

---

### Task 26: Update Main App with Navigation

**Files:**
- Modify: `frontend/src/App.tsx`

**Step 1: Update App.tsx with navigation**

Write to `frontend/src/App.tsx`:
```typescript
import React, { useState } from 'react';
import { ProcessingPage } from './pages/ProcessingPage';
import { HistoryPage } from './pages/HistoryPage';
import { FileText, History } from 'lucide-react';

type Page = 'processing' | 'history';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('processing');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-bold text-gray-900">OCR Platform</h1>

              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setCurrentPage('processing')}
                  className={`
                    flex items-center space-x-2 px-3 py-2 rounded-md transition-colors
                    ${currentPage === 'processing'
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-600 hover:bg-gray-50'
                    }
                  `}
                >
                  <FileText className="w-5 h-5" />
                  <span>Process</span>
                </button>

                <button
                  onClick={() => setCurrentPage('history')}
                  className={`
                    flex items-center space-x-2 px-3 py-2 rounded-md transition-colors
                    ${currentPage === 'history'
                      ? 'bg-blue-50 text-blue-600'
                      : 'text-gray-600 hover:bg-gray-50'
                    }
                  `}
                >
                  <History className="w-5 h-5" />
                  <span>History</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>
        {currentPage === 'processing' && <ProcessingPage />}
        {currentPage === 'history' && <HistoryPage />}
      </main>
    </div>
  );
}

export default App;
```

**Step 2: Commit**

Run:
```bash
git add frontend/src/App.tsx
git commit -m "feat: add navigation between Processing and History pages"
```

Expected: Commit created

---

### Task 27: Build and Test Docker Setup

**Files:**
- None (verification task)

**Step 1: Copy environment file**

Run:
```bash
cp .env.example .env
```

Expected: .env file created

**Step 2: Edit .env with your API keys**

Run:
```bash
nano .env
# OR
vim .env
# OR
open -e .env
```

Add your actual API keys for:
- NEBIUS_API_KEY
- OPENROUTER_API_KEY
- GEMINI_API_KEY

**Step 3: Build Docker containers**

Run:
```bash
docker-compose build
```

Expected: Docker images build successfully (may take 5-10 minutes)

**Step 4: Initialize database**

Run:
```bash
docker-compose run app python database/migrations.py
```

Expected: Database initialized at ./data/ocr_platform.db

**Step 5: Start Docker containers**

Run:
```bash
docker-compose up -d
```

Expected: Containers start successfully

**Step 6: Verify health check**

Run:
```bash
curl http://localhost:8000/health
```

Expected: {"status":"healthy"}

**Step 7: Verify frontend accessible**

Open browser: http://localhost:8000

Expected: OCR Platform loads with Processing page

**Step 8: Test file upload**

1. Navigate to Processing page
2. Upload a test image (JPG/PNG)
3. Select a provider
4. Keep default schema
5. Click "Process Document"

Expected: File uploads successfully, processing starts

**Step 9: Commit environment setup**

Run:
```bash
git add .env.example
git commit -m "docs: add environment configuration instructions"
```

Expected: Commit created

---

### Task 28: Create Documentation

**Files:**
- Create: `README.md`
- Create: `docs/SCHEMA_GUIDE.md`

**Step 1: Create main README**

Write to `README.md`:
```markdown
# OCR Platform

A dockerized OCR platform that processes images and PDFs using Vision Language Models (VLMs) to extract structured data using Pydantic schemas.

## Features

- 📁 **Multi-format Support**: Process images (JPG, PNG) and PDFs
- 🤖 **Multiple VLM Providers**: Nebius, OpenRouter, Google Gemini
- 📝 **Schema Validation**: Define custom schemas or use built-in templates
- 📊 **History & Analytics**: View, filter, and export processing results
- 🐳 **Docker Deployment**: Single command setup with Docker Compose
- 💾 **Data Persistence**: SQLite database with volume mounting

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- API keys for at least one VLM provider

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd ocr_platform_testdrive
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

3. Initialize database:
```bash
docker-compose run app python database/migrations.py
```

4. Start the application:
```bash
docker-compose up
```

5. Open http://localhost:8000 in your browser

### API Keys

Get API keys from:
- **Nebius**: https://nebius.ai/
- **OpenRouter**: https://openrouter.ai/
- **Gemini**: https://ai.google.dev/

## Usage

1. **Upload**: Drag & drop an image or PDF (max 10MB)
2. **Configure**: Select provider and model
3. **Define Schema**: Use built-in templates or create custom schema
4. **Process**: Click "Process Document" to extract data
5. **View Results**: See extracted structured data in real-time
6. **History**: Access past processing jobs in History tab

## Schema Writing

See [SCHEMA_GUIDE.md](docs/SCHEMA_GUIDE.md) for detailed instructions on writing schemas.

## API Documentation

Once running, access API docs at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Project Structure

```
ocr_platform_testdrive/
├── backend/           # FastAPI application
├── frontend/          # React application
├── data/              # SQLite database (gitignored)
├── docker-compose.yml
└── Dockerfile
```

### Stopping the Application

```bash
docker-compose down
```

### Rebuilding

```bash
docker-compose build --no-cache
docker-compose up
```

## Troubleshooting

### Port already in use
Change port in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Database errors
Reinitialize database:
```bash
rm -rf data/
docker-compose run app python database/migrations.py
```

### API key errors
Verify your .env file has correct keys and no extra spaces.

## License

MIT
```

**Step 2: Create Schema Guide**

Write to `docs/SCHEMA_GUIDE.md`:
```markdown
# Schema Writing Guide

This guide explains how to write effective schemas for extracting structured data from documents using the OCR Platform.

## What is a Schema?

A schema defines the structure of data you want to extract from a document. It uses JSON Schema format, which the VLM uses to understand what information to extract and how to format it.

## Basic Schema Structure

```json
{
  "type": "object",
  "properties": {
    "field_name": {
      "type": "string"
    },
    "amount": {
      "type": "number"
    }
  },
  "required": ["field_name"]
}
```

## Data Types

### String
```json
{
  "name": { "type": "string" }
}
```

### Number
```json
{
  "price": { "type": "number" }
}
```

### Boolean
```json
{
  "is_paid": { "type": "boolean" }
}
```

### Array
```json
{
  "items": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "quantity": { "type": "number" }
      }
    }
  }
}
```

### Nested Objects
```json
{
  "address": {
    "type": "object",
    "properties": {
      "street": { "type": "string" },
      "city": { "type": "string" },
      "zip": { "type": "string" }
    }
  }
}
```

## Built-in Templates

The platform includes several built-in templates:

### Invoice
Extracts invoice data including line items, totals, and vendor information.

### Receipt
Extracts receipt data including merchant, items, and payment method.

### ID Document
Extracts ID card information including name, document number, and dates.

### Generic
Extracts free-form text and entities.

## Best Practices

1. **Be Specific**: Use descriptive field names
   ```json
   "invoice_number" vs "id"
   ```

2. **Use Required Fields**: Mark critical fields as required
   ```json
   "required": ["invoice_number", "date", "total"]
   ```

3. **Handle Arrays**: Use arrays for repeating items
   ```json
   "line_items": { "type": "array", ... }
   ```

4. **Test Iteratively**: Start simple, add complexity gradually

5. **Provide Examples**: Include example values in field descriptions
   ```json
   "amount": {
     "type": "number",
     "description": "Total amount in USD, e.g., 123.45"
   }
   ```

## Examples

### Simple Receipt
```json
{
  "type": "object",
  "properties": {
    "merchant": { "type": "string" },
    "date": { "type": "string" },
    "total": { "type": "number" }
  },
  "required": ["merchant", "total"]
}
```

### Complex Invoice
```json
{
  "type": "object",
  "properties": {
    "invoice_number": { "type": "string" },
    "date": { "type": "string" },
    "vendor": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "address": { "type": "string" }
      }
    },
    "line_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "description": { "type": "string" },
          "quantity": { "type": "number" },
          "unit_price": { "type": "number" },
          "total": { "type": "number" }
        },
        "required": ["description", "quantity", "unit_price"]
      }
    },
    "subtotal": { "type": "number" },
    "tax": { "type": "number" },
    "total": { "type": "number" }
  },
  "required": ["invoice_number", "line_items", "total"]
}
```

## Troubleshooting

### Validation Errors
If you see validation errors:
- Check JSON syntax (use JSON linter)
- Ensure all required fields are present
- Verify data types match

### Missing Fields
If extraction misses fields:
- Make the field more descriptive
- Add an example in the description
- Try a different VLM model

### Poor Quality Extraction
- Improve image quality before upload
- Use a more capable model
- Simplify the schema
- Process in smaller sections (for PDFs)

## Tips

1. **Start Simple**: Begin with 3-5 core fields
2. **Iterate**: Add fields incrementally
3. **Test**: Use the same document type for testing
4. **Compare**: Try different providers/models
5. **Save Templates**: Save working schemas as templates
```

**Step 3: Commit documentation**

Run:
```bash
git add README.md docs/SCHEMA_GUIDE.md
git commit -m "docs: add comprehensive README and schema writing guide"
```

Expected: Commit created with documentation

---

## Phase 4: Testing & Polish

### Task 29: Manual Testing

**Files:**
- None (testing task)

**Step 1: Test health endpoint**

Run:
```bash
curl http://localhost:8000/health
```

Expected: `{"status":"healthy"}`

**Step 2: Test providers endpoint**

Run:
```bash
curl http://localhost:8000/api/providers/
```

Expected: JSON with nebius, openrouter, gemini providers

**Step 3: Test file upload**

Run:
```bash
# Create test image
echo "test" > test.txt
mv test.txt test.jpg

# Upload
curl -X POST -F "file=@test.jpg" http://localhost:8000/api/upload/
```

Expected: JSON with file_id, file_name, file_type

**Step 4: Test schemas endpoint**

Run:
```bash
curl http://localhost:8000/api/schemas/templates
```

Expected: Array of built-in templates (Invoice, Receipt, ID, Generic)

**Step 5: Verify frontend loads**

Open: http://localhost:8000

Expected:
- OCR Platform title visible
- Navigation tabs (Process, History)
- File upload zone
- Model selector dropdowns
- Schema editor
- Results panel

**Step 6: Test complete flow**

1. Upload a real image (receipt/invoice)
2. Select Nebius provider
3. Load "Receipt" template
4. Click "Process Document"
5. Wait for completion
6. Verify results display
7. Check History page

Expected: Complete flow works end-to-end

---

### Task 30: Final Cleanup and Optimization

**Files:**
- Modify: `backend/main.py` (add static file serving)
- Create: `frontend/.gitignore`

**Step 1: Update main.py to serve frontend**

Edit `backend/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routers import upload, processing, schemas, jobs, providers

app = FastAPI(title="OCR Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(processing.router)
app.include_router(schemas.router)
app.include_router(jobs.router)
app.include_router(providers.router)

# Serve frontend static files
try:
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
except Exception:
    pass  # Frontend not built in development

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**Step 2: Create frontend .gitignore**

Write to `frontend/.gitignore`:
```gitignore
node_modules
dist
.DS_Store
*.log
.env
.env.local
```

**Step 3: Add docker volumes to .gitignore**

Edit `.gitignore` (add to existing):
```gitignore
# Data
data/
*.db
*.db-journal

# Add at end:
# Docker volumes
docker-volumes/
```

**Step 4: Create final commit**

Run:
```bash
git add .
git commit -m "feat: complete OCR Platform MVP implementation

Implemented:
- Docker multi-stage build with FastAPI + React
- SQLite database with migrations
- File upload with validation (images/PDFs)
- 3 VLM providers: Nebius, OpenRouter, Gemini
- Pydantic schema validation system
- Built-in schema templates (Invoice, Receipt, ID, Generic)
- Processing pipeline with background tasks
- Frontend with Processing and History pages
- Schema editor with CodeMirror
- Real-time processing status
- Job history with filtering

Tech stack:
- Backend: FastAPI, aiosqlite, Pydantic, pdf2image
- Frontend: React 18, TypeScript, Vite, TailwindCSS
- Infrastructure: Docker, Docker Compose, SQLite
"
```

Expected: Final commit created

---

## Success Criteria Verification

### Phase 1: Foundation ✅
- [x] Project scaffolding complete
- [x] Docker multi-stage build configured
- [x] SQLite database with migrations
- [x] Basic FastAPI app with health check
- [x] File upload endpoint
- [x] React frontend with TailwindCSS

### Phase 2: Core Services ✅
- [x] Provider abstraction layer
- [x] Image resizing service
- [x] PDF to image conversion
- [x] Pydantic schema validation
- [x] Schema persistence (CRUD)
- [x] Built-in schema templates
- [x] Processing pipeline
- [x] Error handling

### Phase 3: User Interface ✅
- [x] Model selection dropdowns
- [x] Dynamic parameter editor
- [x] CodeMirror schema editor
- [x] Template selector
- [x] Processing status indicator
- [x] Results display
- [x] Error details view
- [x] File upload with preview

### Phase 4: History & Analytics ✅
- [x] Historical data API
- [x] Dashboard with filters
- [x] Results table
- [x] Job detail view
- [x] Delete functionality
- [x] Status filtering

### Phase 5: Polish & Documentation ✅
- [x] Loading states
- [x] Error messages
- [x] Responsive design
- [x] Environment variable documentation
- [x] README with setup instructions
- [x] Schema writing guide
- [x] Auto-generated API docs

---

**Plan Status: COMPLETE**

**Total Tasks: 30**
**Estimated Time: 15-20 hours**
**Status: Ready for execution**

**Next Steps:**
1. Set up API keys in `.env`
2. Run `docker-compose up`
3. Access http://localhost:8000
4. Process your first document!
