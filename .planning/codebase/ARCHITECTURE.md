# System Architecture

## Overview
OCR Platform is a full-stack web application for extracting structured data from documents using Vision Language Models (VLMs). It follows a classic async web service pattern with background job processing.

## High-Level Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   React SPA     │◄───────►│   FastAPI        │◄───────►│  VLM Providers  │
│  (Frontend)     │  HTTP   │   Backend        │  HTTP   │  (External)     │
│  Port: 5173     │         │  Port: 8000      │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                    │
                                    ▼
                            ┌──────────────────┐
                            │  SQLite DB       │
                            │  (Async)         │
                            └──────────────────┘
```

## Architecture Layers

### Presentation Layer (Frontend)
**Location**: `frontend/src/`

**Components**:
- **Pages**: Route-level views (Processing, History, Methodology)
- **Components**: Reusable UI elements
- **API Client**: Centralized HTTP client (`lib/api.ts`)

**Patterns**:
- Functional components with React hooks
- Unidirectional data flow (props down, events up)
- Controlled form inputs
- Optimistic UI updates with polling fallback

**State Management**:
- Local component state (useState, useEffect)
- No global state management (Redux/Zustand not used)
- Server state via polling

---

### Application Layer (Backend)
**Location**: `backend/routers/`, `backend/services/`

**Routers** (API Endpoints):
- `upload.py` - File upload and storage
- `processing.py` - Job submission and management
- `schemas.py` - Schema CRUD operations
- `jobs.py` - Job status and history
- `providers.py` - Provider and model listing
- `text_processing.py` - Text-based extraction

**Services** (Business Logic):
- `processing.py` - Main processing pipeline orchestrator
- `document_classifier.py` - Document analysis and routing
- `text_extraction.py` - PDF text extraction
- `vlm_provider.py` - Abstract VLM provider interface
- `nebius.py`, `openrouter.py`, `gemini.py` - Provider implementations
- `schema_service.py` - JSON schema validation
- `image_service.py` - Image conversion and resizing

---

### Data Layer
**Location**: `backend/database/`

**Components**:
- `crud.py` - Async database operations
- `migrations.py` - Database schema initialization

**Database**: SQLite with aiosqlite (async)

**Tables**:
- `schemas` - JSON schema definitions
- `processing_jobs` - Job records with status/results
- `uploaded_files` - File metadata tracking

---

## Data Flow

### Vision Extraction Pipeline

```
User Upload → API → File Storage → Job Created → Background Worker
                                                      │
                                                      ▼
                                            PDF to Images (if needed)
                                                      │
                                                      ▼
                                          Image Resize → Encode Base64
                                                      │
                                                      ▼
                                          VLM API Call (with schema)
                                                      │
                                                      ▼
                                          JSON Validation → Save Result
                                                      │
                                                      ▼
                                            Frontend Polls → Display
```

**Key Points**:
- Upload is synchronous (returns immediately)
- Processing is asynchronous (background job)
- Frontend polls job status every 2 seconds
- Results stored in SQLite for history

---

### Text Extraction Pipeline

```
User Upload → API → File Storage → Job Created → Background Worker
                                                      │
                                                      ▼
                                  Document Classifier (check text layer)
                                                      │
                                                      ▼
                                pdfplumber extracts raw text
                                                      │
                                                      ▼
                                      LLM API Call (text-only)
                                                      │
                                                      ▼
                                      JSON Validation → Save Result
```

**Key Points**:
- 87x faster than vision pipeline (per doc comments)
- 90% cheaper (no image processing)
- Only works for PDFs with extractable text
- Falls back to vision pipeline for image-based PDFs

---

## Processing Modes

### Auto-Routing (Document Classification)
**Service**: `backend/services/document_classifier.py`

**Decision Tree**:
```
PDF with text layer + high density → Text extraction
PDF with images + high complexity  → Vision extraction
Mixed content                      → Vision extraction
Scanned simple                     → Vision extraction
Scanned complex                   → Vision extraction
```

**Metrics**:
- Text density (chars per page)
- Page count
- Image count
- Table count
- Complexity score (0-100)

**Output**: `DocumentAnalysis` with recommended pipeline

---

### Manual Mode Selection
**Frontend**: `frontend/src/components/ExtractionModeSelector.tsx`

**Options**:
- Vision Extraction - VLM processes images
- Text Extraction - pdfplumber + LLM

**User Override**: User can bypass auto-routing

---

## Async Job Processing

### Job Lifecycle
```
pending → processing → success/error
            │
            └─► (background worker)
```

**Entry Points**:
- `run_processing_job()` - Vision pipeline
- `run_text_processing_job()` - Text pipeline

**Status Updates**:
- Database updated at each stage
- Frontend polls `/api/jobs/{id}` endpoint
- UI shows real-time progress

---

## Abstractions

### VLM Provider Interface
**Location**: `backend/services/vlm_provider.py`

**Abstract Methods**:
```python
async def process_image(image, prompt, schema, **kwargs) -> Dict
async def process_text(text, prompt, schema, model, **kwargs) -> Dict
def get_models() -> List[str]
def get_default_image_size() -> Tuple[int, int]
```

**Implementations**:
- `NebiusProvider`
- `OpenRouterProvider`
- `GeminiProvider`

**Benefits**:
- Swap providers without changing business logic
- Consistent error handling
- Unified response format

---

### Schema Service
**Location**: `backend/services/schema_service.py`

**Capabilities**:
- Validate extracted data against JSON schema
- Built-in templates (Invoice, Receipt, ID Card, Generic)
- Custom schema support
- Double-encoded JSON handling

**Templates**: Stored as constant dictionaries

---

## Error Handling Strategy

### Validation Layers
1. **File Upload** - Size, type validation
2. **Schema** - JSON schema format validation
3. **API Keys** - Provider key existence check
4. **Response** - JSON parsing + schema validation
5. **Processing** - Try/catch with error status updates

### Error Propagation
```
Provider Error → Job Status: "error"
               → Error message stored
               → Frontend displays error
```

### Graceful Degradation
- Empty PDF text → Suggest vision pipeline
- Provider timeout → Return error (no retry currently)
- Invalid JSON → Return raw response for debugging

---

## Security Considerations

### Current Implementation
- CORS: Wide-open (`allow_origins=["*"]`)
- Auth: None (single-user assumption)
- File upload: Size limit only (10MB default)
- SQL injection: Mitigated by parameterized queries
- XSS: React escaping by default

### Known Gaps
- No authentication/authorization
- No rate limiting
- API keys in environment variables (plaintext)
- No input sanitization beyond type validation

---

## Performance Characteristics

### Bottlenecks
1. **VLM API Latency** - 3-30 seconds per request
2. **PDF to Image Conversion** - 1-5 seconds for large PDFs
3. **Database Writes** - Minimal (SQLite on local disk)

### Optimizations
- Async I/O throughout (FastAPI, aiosqlite, httpx)
- Image resizing before API calls
- Text extraction for digital PDFs (87x faster)
- Connection pooling via httpx.AsyncClient

### Scalability Constraints
- SQLite is single-writer (concurrent jobs may queue)
- No worker pool (jobs run in FastAPI event loop)
- No horizontal scaling (single server only)

---

## Extension Points

### Adding a New VLM Provider
1. Create `backend/services/{provider}.py`
2. Inherit from `VLMProvider`
3. Implement abstract methods
4. Add to `ProcessingService.providers` dict
5. Add API key to `config.py`

### Adding a New Processing Pipeline
1. Create service in `backend/services/`
2. Create job runner function (like `run_text_processing_job`)
3. Add router endpoint in `backend/routers/`
4. Update frontend to call new endpoint

### Adding a New Schema Template
1. Edit `backend/services/schema_service.py`
2. Add to `get_builtin_templates()` dict
3. Frontend automatically discovers via `/api/schemas/templates`
