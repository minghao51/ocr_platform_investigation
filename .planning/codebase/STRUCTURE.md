# Directory Structure

## Project Root Layout

```
ocr_platform_testdrive/
├── backend/              # FastAPI application
├── frontend/             # React application
├── docs/                 # Project documentation
├── .planning/            # Planning documents (generated)
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore rules
├── docker-compose.yml   # Docker orchestration
├── Dockerfile           # Container image
└── README.md            # Project overview
```

---

## Backend Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── config.py                  # Pydantic settings
├── pyproject.toml            # UV dependencies
├── routers/                  # API endpoints
│   ├── __init__.py
│   ├── upload.py             # File upload endpoint
│   ├── processing.py         # Job submission
│   ├── schemas.py            # Schema CRUD
│   ├── jobs.py               # Job status/history
│   ├── providers.py          # Provider/model listing
│   └── text_processing.py    # Text extraction endpoint
├── services/                 # Business logic
│   ├── __init__.py
│   ├── processing.py         # Main pipeline orchestrator
│   ├── document_classifier.py # PDF analysis & routing
│   ├── text_extraction.py    # pdfplumber text extraction
│   ├── vlm_provider.py       # Abstract VLM interface
│   ├── nebius.py            # Nebius provider
│   ├── openrouter.py        # OpenRouter provider
│   ├── gemini.py            # Gemini provider
│   ├── image_service.py     # Image conversion/encoding
│   ├── schema_service.py    # JSON schema validation
│   └── paddle_ocr_service.py # OCR (unused, ARM64 issue)
├── database/                 # Data layer
│   ├── __init__.py
│   ├── crud.py              # Async DB operations
│   └── migrations.py        # DB schema initialization
├── models/                   # Pydantic models
│   ├── __init__.py
│   ├── providers.py         # Provider-related models
│   └── schemas.py           # Schema-related models
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── test_integration.py  # End-to-end tests
│   ├── test_schema_service.py
│   ├── test_image_service.py
│   └── test_fix_result_parsing.py
├── scripts/                  # Utility scripts
│   ├── __init__.py
│   ├── batch_test_parsing.py
│   ├── test_schema_parsing.py
│   ├── test_document_classifier.py
│   └── test_upload.py
└── data/                     # SQLite database (gitignored)
    └── ocr_platform.db
```

### Key Backend Files by Purpose

**Entry Point**:
- `main.py` - App initialization, middleware, router inclusion

**Configuration**:
- `config.py` - Environment-based settings

**HTTP Layer**:
- `routers/*.py` - API endpoint definitions

**Business Logic**:
- `services/processing.py` - Core extraction pipeline (414 lines)
- `services/document_classifier.py` - PDF analysis (283 lines)
- `services/text_extraction.py` - Text extraction

**Provider Integrations**:
- `services/vlm_provider.py` - Base provider class
- `services/{nebius,openrouter,gemini}.py` - Provider implementations

**Data Access**:
- `database/crud.py` - Database operations (187 lines)

---

## Frontend Structure

```
frontend/
├── index.html                # HTML entry point
├── package.json             # npm dependencies
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript config
├── tsconfig.node.json       # TypeScript config for Node
├── postcss.config.js        # PostCSS (Tailwind) config
├── eslint.config.js         # ESLint rules
├── src/
│   ├── main.tsx             # React entry point
│   ├── App.tsx              # Root component (navigation)
│   ├── lib/
│   │   └── api.ts           # API client (213 lines)
│   ├── components/          # Reusable components
│   │   ├── FileUpload.tsx
│   │   ├── ModelSelector.tsx (152 lines)
│   │   ├── SchemaEditor.tsx (353 lines)
│   │   ├── ExtractionModeSelector.tsx (162 lines)
│   │   ├── AdvancedOptions.tsx (144 lines)
│   │   ├── ProcessingStatus.tsx
│   │   ├── ResultsDisplay.tsx (134 lines)
│   │   ├── ExtractedDataDisplay.tsx
│   │   └── ProcessingStatus.tsx (126 lines)
│   └── pages/               # Route-level components
│       ├── ProcessingPage.tsx (41 lines)
│       ├── BaseExtractionPage.tsx (284 lines)
│       ├── HistoryPage.tsx (197 lines)
│       └── MethodologyPage.tsx (330 lines)
└── dist/                    # Build output (gitignored)
```

### Key Frontend Files by Purpose

**Entry Points**:
- `index.html` - HTML shell
- `src/main.tsx` - React mount

**Layout**:
- `src/App.tsx` - Navigation and routing (simple conditional render)

**API Integration**:
- `src/lib/api.ts` - Centralized HTTP client (213 lines)

**Main Features**:
- `src/pages/BaseExtractionPage.tsx` - Core extraction UI (284 lines)
- `src/pages/HistoryPage.tsx` - Job history (197 lines)
- `src/pages/MethodologyPage.tsx` - Documentation page (330 lines)

**Complex Components**:
- `src/components/SchemaEditor.tsx` - JSON schema editor (353 lines)
- `src/components/ExtractionModeSelector.tsx` - Mode selection (162 lines)
- `src/components/ModelSelector.tsx` - Provider/model selection (152 lines)

---

## Documentation Structure

```
docs/
├── guides/                  # User documentation
│   ├── setup.md            # Installation & configuration
│   ├── user-guide.md       # How to use the platform
│   ├── schema-guide.md     # Creating custom schemas
│   ├── troubleshooting.md  # Common issues
│   └── api.md              # API reference
├── development/             # Developer docs
│   ├── testing-guide.md    # Testing procedures
│   ├── backend-testing.md  # Backend-specific testing
│   └── auto-routing-test-report.md
├── implementation/          # Technical docs
│   ├── implementation-summary.md
│   ├── mvp-implementation.md
│   └── auto-routing.md
├── plans/                   # Design documents
├── progress/                # Project tracking
└── reports/                 # Historical records
    ├── changelog.md
    └── investigations/
```

---

## Naming Conventions

### Python (Backend)
- **Files**: `snake_case.py` (e.g., `vlm_provider.py`, `text_extraction.py`)
- **Classes**: `PascalCase` (e.g., `VLMProvider`, `ProcessingService`)
- **Functions/Methods**: `snake_case` (e.g., `process_image`, `get_job`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `COMPLEXITY_THRESHOLD_SIMPLE`)
- **Private methods**: Leading underscore (e.g., `_process_pdf`)

### TypeScript/React (Frontend)
- **Files**: `PascalCase.tsx` for components, `snake_case.ts` for utilities
- **Components**: `PascalCase` (e.g., `FileUpload`, `ModelSelector`)
- **Functions**: `camelCase` (e.g., `handleSubmit`, `fetchJobStatus`)
- **Hooks**: `use` prefix (e.g., `useState`, `useEffect` - built-in)
- **Types/Interfaces**: `PascalCase` (e.g., `Job`, `Provider`)

### Database
- **Tables**: `snake_case` (e.g., `processing_jobs`, `uploaded_files`)
- **Columns**: `snake_case` (e.g., `file_name`, `processing_time_seconds`)
- **Foreign keys**: `{table}_id` pattern (e.g., `schema_id`)

### API Routes
- **Path**: `/api/{resource}/{action}` (e.g., `/api/jobs/123`)
- **Methods**: RESTful (GET, POST, DELETE)
- **Query params**: `snake_case` (e.g., `?status=success&limit=10`)

---

## File Organization Patterns

### Backend Patterns
- **Routers**: One file per resource domain
- **Services**: One file per major capability
- **Tests**: `test_{name}.py` naming
- **Scripts**: Descriptive names with `test_` prefix for test scripts

### Frontend Patterns
- **Pages**: `{Name}Page.tsx` in `pages/` directory
- **Components**: Descriptive name in `components/` directory
- **Utilities**: `lib/` directory for shared code
- **Types**: Inline in component files (no separate types directory)

---

## Build Artifacts & Generated Files

**Backend**:
- `.venv/` - Python virtual environment (gitignored)
- `data/ocr_platform.db` - SQLite database (gitignored)

**Frontend**:
- `dist/` - Vite build output (gitignored)
- `node_modules/` - npm dependencies (gitignored)

**Planning**:
- `.planning/codebase/` - Generated documentation (this file)

---

## Configuration Files

**Root Level**:
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore rules
- `docker-compose.yml` - Multi-container setup
- `Dockerfile` - Container image definition

**Backend**:
- `pyproject.toml` - Python dependencies and metadata

**Frontend**:
- `package.json` - Node dependencies and scripts
- `vite.config.ts` - Vite build configuration
- `tsconfig.json` - TypeScript compiler options
- `postcss.config.js` - TailwindCSS configuration
- `eslint.config.js` - Linting rules
