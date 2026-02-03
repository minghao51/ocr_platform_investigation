# Technology Stack

## Overview
OCR Platform uses a modern Python/JavaScript stack with emphasis on async processing, type safety, and rapid development.

## Languages

### Backend
- **Python 3.11+** (requires >=3.11)
  - Type hints used throughout
  - Async/await for I/O operations
  - Dataclasses for structured data

### Frontend
- **TypeScript 5.5+** (strict mode enabled)
  - ES2020 target
  - React 18 with functional components and hooks

## Runtime & Build Tools

### Backend
- **uv** - Fast Python package manager and project manager
- **Uvicorn 0.32.0** - ASGI server with standard features
- **Hatchling** - Build backend for Python packages

### Frontend
- **Vite 5.3.1** - Fast dev server and optimized builds
- **@vitejs/plugin-react 4.3.1** - React support for Vite
- **ESBuild** - Bundled with Vite for fast transpilation

## Frameworks

### Backend
- **FastAPI 0.115.0** - Modern async web framework
  - Automatic OpenAPI documentation
  - Type-based request/response validation
  - CORS middleware
  - Static file serving

### Frontend
- **React 18.3.1** - UI library with hooks
- **React DOM 18.3.1** - React DOM renderer
- **TailwindCSS 3.4.4** - Utility-first CSS framework
  - PostCSS 8.4.39 for processing
  - Autoprefixer 10.4.19 for browser compatibility

## Key Dependencies

### Backend Core
```
fastapi==0.115.0          # Web framework
uvicorn[standard]==0.32.0 # ASGI server
pydantic==2.10.0          # Data validation
pydantic-settings==2.6.0  # Config management
httpx==0.28.0             # Async HTTP client
aiosqlite==0.20.0         # Async SQLite
python-multipart==0.0.12  # Form data parsing
python-dotenv==1.0.1      # Environment variables
```

### Document Processing
```
pdf2image==1.17.0         # PDF to image conversion
pillow==11.0.0            # Image processing
pdfplumber>=0.11.0        # PDF text extraction
pymupdf>=1.26.7           # Fast PDF analysis (fitz)
jsonschema>=4.26.0        # JSON schema validation
```

### Frontend Core
```
react==18.3.1             # UI library
react-dom==18.3.1         # React renderer
react-simple-code-editor==0.14.1  # Code editor component
prismjs==1.30.0           # Syntax highlighting
```

### Frontend Dev
```
typescript==5.5.3              # TypeScript compiler
@vitejs/plugin-react==4.3.1    # Vite React plugin
eslint==8.57.0                 # Linting
@typescript-eslint/*==7.13.1   # TypeScript ESLint rules
eslint-plugin-react-hooks==4.6.2
eslint-plugin-react-refresh==0.4.7
```

## Infrastructure

### Containerization
- **Docker** - Container runtime
- **Docker Compose** - Multi-container orchestration

### Database
- **SQLite** (aiosqlite) - Embedded async database
  - Database file: `./data/ocr_platform.db`
  - migrations in `backend/database/migrations.py`

## Development Tools

### Backend Testing
```
pytest>=7.4.0              # Test framework
pytest-asyncio>=0.21.0     # Async test support
httpx>=0.24.0              # Test client
```

### Frontend Tooling
- **ESLint** - Linting with React/TypeScript rules
- **TypeScript Compiler** - Type checking and transpilation
- **Vite Dev Server** - Hot module replacement, proxy to backend

## Configuration

### Environment
- `.env` file for environment variables
- `.env.example` as template
- Loaded via `python-dotenv`

### TypeScript Config
- Target: ES2020
- Module: ESNext (bundler mode)
- Strict mode enabled
- Path aliases: `@/*` → `src/*`

### Build Config
- Backend: `backend/pyproject.toml` (uv-based)
- Frontend: `frontend/package.json` (npm-based)

## Version Control
- Git repository with `.gitignore` for:
  - `.venv/` (Python virtual env)
  - `node_modules/` (Node dependencies)
  - `.env` (Environment secrets)
  - `data/` (SQLite database)
  - `dist/` (Build artifacts)

## Deployment

### Docker
- Multi-stage builds for production
- Backend serves frontend static files
- Single container deployment option

### Local Development
- Backend: `uv run uvicorn main:app --reload --port 8000`
- Frontend: `npm run dev` (proxies to backend on port 8000)
