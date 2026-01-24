# Project Structure

Detailed directory structure and file organization for the OCR Platform.

## Directory Tree

```
ocr_platform_testdrive/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Pydantic settings management
│   ├── pyproject.toml             # Python dependencies (uv)
│   ├── requirements.txt           # Python dependencies (pip)
│   ├── routers/                   # API route handlers
│   │   ├── upload.py              # File upload endpoint
│   │   ├── processing.py          # Document processing & job status
│   │   ├── schemas.py             # Schema CRUD operations
│   │   ├── jobs.py                # Job history management
│   │   ├── providers.py           # Provider listing
│   │   └── text_processing.py     # Text extraction endpoint
│   ├── services/                  # Business logic layer
│   │   ├── vlm_provider.py        # Base VLM provider class
│   │   ├── nebius.py              # Nebius provider implementation
│   │   ├── openrouter.py          # OpenRouter provider implementation
│   │   ├── gemini.py              # Gemini provider implementation
│   │   ├── image_service.py       # Image processing utilities
│   │   ├── schema_service.py      # Schema validation logic
│   │   ├── processing.py          # Main processing pipeline
│   │   ├── text_extraction.py     # Text extraction pipeline
│   │   └── document_classifier.py # Document classification for auto-routing
│   ├── database/                  # Database layer
│   │   ├── schema.sql             # Database schema definition
│   │   ├── migrations.py          # DB initialization script
│   │   └── crud.py                # Database CRUD operations
│   ├── models/                    # Pydantic models
│   │   └── schemas.py             # Request/response models
│   ├── data/                      # SQLite database storage (gitignored)
│   │   └── ocr.db                 # Default database file
│   └── tests/                     # Backend tests
│       ├── test_services/         # Service layer tests
│       └── test_integration.py    # Integration tests
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx               # React entry point
│   │   ├── App.tsx                # Main app with routing
│   │   ├── lib/
│   │   │   └── api.ts             # API client (httpx-like)
│   │   ├── components/            # Reusable UI components
│   │   │   ├── FileUpload.tsx     # File upload component
│   │   │   ├── ModelSelector.tsx  # Provider/model selection
│   │   │   ├── SchemaEditor.tsx   # JSON schema editor
│   │   │   ├── ResultsDisplay.tsx # Display extraction results
│   │   │   └── ProcessingStatus.tsx # Job status polling
│   │   └── pages/                 # Page components
│   │       ├── ProcessingPage.tsx # Main processing interface
│   │       ├── HistoryPage.tsx    # Job history view
│   │       └── TextExtractionPage.tsx # Text extraction UI
│   ├── public/                    # Static assets
│   ├── package.json               # Node dependencies
│   ├── vite.config.ts             # Vite configuration
│   └── tailwind.config.js         # TailwindCSS configuration
│
├── docs/                          # Documentation
│   ├── guides/                    # User-facing documentation
│   │   ├── setup.md               # Setup instructions
│   │   ├── user-guide.md          # Usage guide
│   │   ├── schema-guide.md        # JSON schema creation
│   │   ├── troubleshooting.md     # Common issues
│   │   └── api.md                 # API reference
│   ├── development/               # Developer documentation
│   │   ├── testing-guide.md       # Testing procedures
│   │   ├── backend-testing.md     # Backend-specific testing
│   │   └── test-report.md         # Test results
│   ├── implementation/            # Technical details
│   │   ├── overview.md            # Project summary
│   │   ├── mvp-complete.md        # MVP implementation report
│   │   ├── auto-routing.md        # Auto-routing feature
│   │   └── project-structure.md   # This file
│   ├── plans/                     # Design documents
│   ├── progress/                  # Project tracking
│   └── reports/                   # Historical records
│
├── Dockerfile                     # Multi-stage Docker build
├── docker-compose.yml             # Docker Compose configuration
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── README.md                      # Project overview
└── claude.md                      # Developer context guide
```

## Backend Architecture

### Routers (`backend/routers/`)
Each router handles a specific domain of the API:
- **upload.py**: Validates and stores uploaded files
- **processing.py**: Orchestrates VLM processing with job management
- **schemas.py**: Manages custom schema CRUD operations
- **jobs.py**: Provides job history and filtering
- **providers.py**: Returns available providers and models
- **text_processing.py**: Handles text extraction pipeline

### Services (`backend/services/`)
Business logic is separated from route handlers:
- **vlm_provider.py**: Abstract base class defining provider interface
- **nebius.py, openrouter.py, gemini.py**: Provider-specific implementations
- **processing.py**: Main pipeline for vision-based extraction
- **text_extraction.py**: Pipeline for text-based extraction
- **document_classifier.py**: Determines optimal extraction method
- **schema_service.py**: Validates JSON schemas against user data
- **image_service.py**: Converts PDFs to images and prepares them for VLMs

### Database (`backend/database/`)
- **schema.sql**: SQL schema for jobs, schemas, and uploads tables
- **migrations.py**: Creates tables and indexes on first run
- **crud.py**: Async database operations using aiosqlite

## Frontend Architecture

### Component Structure
Components are organized by responsibility:
- **Pages**: Top-level route components (ProcessingPage, HistoryPage, etc.)
- **Shared Components**: Reusable UI elements (FileUpload, ModelSelector, etc.)
- **API Client**: Centralized HTTP client in `lib/api.ts`

### State Management
The frontend uses React's built-in state management:
- Local component state for UI interactions
- Effect-based polling for job status updates
- Props drilling for data flow (no global state library)

### Styling
- **TailwindCSS**: Utility-first CSS framework
- **Responsive Design**: Mobile-first approach
- **Component-scoped**: Styles defined within components

## Data Flow

### Document Processing Flow

1. **Upload** (`POST /api/upload`)
   - `routers/upload.py` validates file
   - Stored in temporary location
   - Returns file path

2. **Processing** (`POST /api/process`)
   - `routers/processing.py` creates job record
   - `services/document_classifier.py` analyzes document
   - Routes to vision or text pipeline
   - Background job starts processing

3. **Vision Pipeline** (if needed)
   - `services/processing.py` orchestrates extraction
   - `services/image_service.py` prepares images
   - Provider service (Nebius/OpenRouter/Gemini) calls VLM API
   - `services/schema_service.py` validates response

4. **Text Pipeline** (if applicable)
   - `services/text_extraction.py` extracts text from PDF
   - `services/paddle_ocr_service.py` provides OCR layer
   - Returns structured text data

5. **Result Retrieval** (`GET /api/process/status/{job_id}`)
   - `routers/processing.py` queries database
   - Returns job status and results
   - Frontend polls until completion

## Configuration

### Environment Variables (.env)
- Provider API keys (NEBIUS_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY)
- Database path (DATABASE_URL)
- Upload size limit (MAX_UPLOAD_SIZE)

### Application Settings (backend/config.py)
- Pydantic-based configuration
- Validates environment variables
- Provides defaults for optional settings

## Development Workflow

See [claude.md](../claude.md) for:
- Development setup instructions
- Common development tasks
- Testing procedures
- Troubleshooting development issues

## Extension Points

### Adding New VLM Providers
1. Create new provider service in `backend/services/`
2. Inherit from `VLMProvider` base class
3. Implement `process()` method
4. Register in `backend/routers/providers.py`

### Adding New Schemas
1. Create JSON schema following [schema guide](../guides/schema-guide.md)
2. Add to `backend/services/schema_service.py` templates
3. Or create custom schema via UI

### Adding New Frontend Pages
1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Update navigation if needed
