# OCR/VLM Testing Platform - Design Document

## Project Overview

A local, Docker-containerized web application for testing and comparing OCR/Vision Language Model capabilities across multiple providers (Nebius, OpenRouter, Gemini) with flexible Pydantic schema validation and comprehensive local logging.

**Core Objectives:**
- Unified interface to test different VLM/OCR models on various document types
- Flexible data extraction using user-defined, complex Pydantic schemas
- Complete historical records with full error logging for analysis
- Intuitive drag-and-drop interface with configuration options and dashboard
- Schema persistence with customizable templates
- Multi-page PDF processing with merged results

## Key Design Decisions

### 1. Schema Validation Strategy
**Choice:** Use Pydantic v2 `TypeAdapter` for runtime schema validation

**Rationale:**
- Safer than `eval()` - no code execution risks
- More flexible than templates - supports dynamic user schemas
- Full support for complex schemas: nested models, unions, generics, validators
- Excellent error messages for debugging

**Implementation:**
```python
from pydantic import TypeAdapter
import json

# User provides JSON schema definition
schema_def = await request.json()
adapter = TypeAdapter(schema_def)
validated_data = adapter.validate_python(raw_vlm_response)
```

### 2. VLM API Integration
**Choice:** Universal prompt format with provider-specific adapters

**Architecture:**
```
BaseProvider (abstract)
├── NebiusProvider
├── OpenRouterProvider
└── GeminiProvider
```

Each provider implements:
- `prepare_prompt(schema, image_base64)` -> format-specific prompt
- `send_request(prompt, config)` -> provider API call
- `parse_response(response)` -> standardized dict

**Prompt Strategy:**
- Inject JSON schema definition into system prompt
- Request structured JSON output matching schema
- For providers with structured output APIs (Gemini), use native features
- Fallback to prompt-based JSON extraction for others

### 3. Multi-Page PDF Handling
**Choice:** Process all pages, merge results into array

**Implementation:**
- Use `pdf2image` to convert PDF → list of PIL Images
- Each page sent to VLM separately
- Results aggregated into list: `[{page_1_data}, {page_2_data}, ...]`
- Schema definition wrapped in array context for validation

**Workflow:**
```
PDF upload → pdf2image → [page1.png, page2.png, ...]
    ↓
For each page:
    - Resize to VLM optimal dimensions
    - Convert to base64
    - Send to VLM
    - Validate against schema
    ↓
Merge results: [{page1: {...}}, {page2: {...}}]
```

### 4. Image Resizing Strategy
**Choice:** Smart resize per provider without enhancement

**Provider Optimal Sizes:**
- **Gemini Pro Vision**: 2048x2048 max, maintains aspect ratio
- **OpenRouter models**: Varies, typically 1536x1536 or 2048x2048
- **Nebius**: Documentation-dependent, default to 2048x2048

**Implementation:**
```python
def resize_for_provider(image: Image, provider: str) -> Image:
    max_dim = PROVIDER_MAX_DIMS.get(provider, 2048)
    if max(image.size) <= max_dim:
        return image
    image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    return image
```

**Key Constraints:**
- No enhancement (no denoising, contrast adjustment, etc.)
- Maintain aspect ratio
- Use high-quality resampling (LANCZOS)
- Only downscale, never upscale

### 5. Schema Persistence
**Choice:** Dedicated `schemas` table with template support

**Features:**
- User-created schemas: Custom name, description, definition
- Built-in templates: Pre-loaded with `is_template=1`
- Version tracking: `created_at`, `updated_at` timestamps
- Referential integrity: Jobs reference schema_id, cascade on delete
- Historical preservation: Jobs store schema_definition snapshot

**Template Schemas:**
1. **Invoice**: vendor, date, total, line_items[], tax, etc.
2. **Receipt**: merchant, date, items[], total, payment_method
3. **ID Document**: name, id_number, dob, expiration, issuing_country
4. **Generic Document**: title, content, metadata, extracted_entities

### 6. Frontend Architecture
**Choice:** React 18 + TypeScript + Vite, lightweight state management

**State Management:**
- React Context for global state (current file, processing status)
- `useReducer` for complex workflows (schema editor, model config)
- No Redux/Zustand - overkill for single-user local app

**Component Structure:**
```
App
├── ProcessingPage
│   ├── FileUploadPanel
│   ├── ModelConfigPanel
│   │   ├── ProviderSelector
│   │   ├── ModelSelector
│   │   └── ParameterEditor
│   ├── SchemaEditorPanel
│   │   ├── TemplateSelector
│   │   ├── CodeMirrorEditor
│   │   └── SaveSchemaForm
│   └── ResultsPanel
│       ├── ProcessingStatus
│       └── ResultDisplay
└── HistoryPage
    ├── FilterPanel
    ├── ResultsTable
    └── DetailModal
```

**Editor Choice:** CodeMirror 6 (not Monaco)
- Lighter bundle size (~200KB vs 8MB)
- Excellent JSON syntax highlighting
- Built-in linting with jsonlint
- Better performance for single-file editor

### 7. Error Handling Strategy
**Choice:** Multi-stage validation with specific error codes

**Validation Stages:**
1. **File Upload**
   - `INVALID_FILE_TYPE` - unsupported format
   - `FILE_TOO_LARGE` - exceeds 10MB
   - `CORRUPT_FILE` - cannot be read

2. **Schema Validation**
   - `INVALID_JSON` - malformed JSON in schema definition
   - `INVALID_PYDANTIC_SCHEMA` - not a valid Pydantic schema
   - `SCHEMA_VALIDATION_FAILED` - VLM output doesn't match schema (with details)

3. **VLM Processing**
   - `VLM_API_ERROR` - provider API failure (with raw response)
   - `VLM_INVALID_JSON` - model didn't return valid JSON
   - `VLM_TIMEOUT` - request exceeded timeout
   - `VLM_RATE_LIMITED` - provider rate limit (optional handling)

**Error Response Format:**
```json
{
  "success": false,
  "error_code": "SCHEMA_VALIDATION_FAILED",
  "message": "User-friendly error message",
  "details": {
    "validation_errors": ["field path: error detail"],
    "raw_vlm_response": "...",
    "schema_definition": {...}
  }
}
```

### 8. Export Functionality
**Choice:** Export logs and results to JSON/CSV

**Export Features:**
- **Export All**: Dump entire database to JSON (backup)
- **Export Filtered**: Export current filtered results to CSV/JSON
- **Export Single Job**: Export individual job with all metadata
- **Include/Exclude**:
  - Raw VLM responses (large, optional)
  - File previews (base64, very large)
  - Schema definitions

**Implementation:**
```python
@router.get("/export")
async def export_jobs(
    format: str = "json",  # json or csv
    include_raw: bool = False,
    filters: JobFilters = None
):
    jobs = await fetch_jobs(filters)
    if format == "csv":
        return CSVResponse(jobs, include_raw=include_raw)
    return JSONResponse({"jobs": jobs, "include_raw": include_raw})
```

## Technical Architecture

### Backend Stack (Python/FastAPI)
```
Dependencies:
├── fastapi + uvicorn (web server)
├── pydantic>=2.0 (schema validation)
├── httpx (async HTTP client)
├── aiosqlite (async database)
├── python-multipart (file uploads)
├── python-dotenv (environment)
├── pdf2image (PDF → image conversion)
├── pillow (image processing)
├── pydantic-settings (config management)
└── python-jose (cryptography, if needed later)
```

### Frontend Stack (React/TypeScript)
```
Dependencies:
├── react@18 + vite (framework + build)
├── typescript (type safety)
├── @uiw/react-codemirror (schema editor)
├── react-dropzone (file upload)
├── axios (HTTP client)
├── react-table (table display)
├── tailwindcss (styling)
├── lucide-react (icons)
└── date-fns (date formatting)
```

### Docker Architecture
```
docker-compose.yml:
  services:
    app:
      build: .
      ports:
        - "8000:8000"
      volumes:
        - ./data:/app/data  # SQLite persistence
      environment:
        - NEBIUS_API_KEY=${NEBIUS_API_KEY}
        - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
        - GEMINI_API_KEY=${GEMINI_API_KEY}
        - DATABASE_PATH=/app/data/ocr_platform.db
```

**Multi-stage Dockerfile:**
```dockerfile
# Stage 1: Frontend build
FROM node:18-alpine as frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend runtime
FROM python:3.11-slim
WORKDIR /app
# Install system dependencies (Poppler for pdf2image)
RUN apt-get update && apt-get install -y poppler-utils
# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./static
# Install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Database Schema

See `database/schema.sql` for complete SQL definition.

**Key Tables:**
1. **schemas**: Persistent schema definitions with templates
2. **processing_jobs**: Main log of all processing attempts

**Indexes:**
- `idx_jobs_created_at`: For time-based queries
- `idx_jobs_status`: For success/failed filtering
- `idx_jobs_model_provider`: For provider comparison
- `idx_jobs_file_type`: For document type analysis

## Security Considerations

### Local-Only Security
- No authentication required (local-only use)
- API keys in environment variables only (never in code)
- No file path traversal vulnerabilities (validated filenames)
- File size limits strictly enforced (10MB)

### Input Validation
- File type whitelist: PDF, JPG, JPEG, PNG, BMP, TIFF, WEBP
- Schema size limits: Max 1MB schema definition
- VLM configuration bounds: reasonable ranges for temp, tokens, etc.
- SQL injection prevention: Use parameterized queries only

### API Key Management
```bash
# .env file (gitignored)
NEBIUS_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
GEMINI_API_KEY=AIza...

# Loaded in FastAPI via pydantic-settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    nebius_api_key: str
    openrouter_api_key: str
    gemini_api_key: str

    class Config:
        env_file = ".env"
```

## Performance Considerations

### Async Operations
- All database queries use `aiosqlite`
- VLM API calls use `httpx.AsyncClient`
- File I/O is async where possible
- Multiple pages processed concurrently (with rate limiting if needed)

### Caching Strategy
- No caching by default (fresh results each time)
- Optional: Cache provider model lists (change infrequently)
- Optional: Cache schema validation results (same schema reused)

### Database Optimization
- SQLite sufficient for single-user local app
- Indexes on all filter columns
- VACUUM on delete to reclaim space
- Consider WAL mode for better concurrency

## Testing Strategy

### Unit Tests
- Schema validation logic
- Provider adapter formatting
- Image resizing logic
- Error code generation

### Integration Tests
- End-to-end API workflows
- Database CRUD operations
- File upload processing
- Multi-page PDF handling

### Manual Testing Checklist
- [ ] Upload each supported file type
- [ ] Test with each VLM provider
- [ ] Create and save custom schema
- [ ] Use built-in templates
- [ ] Process multi-page PDF
- [ ] Export results to JSON/CSV
- [ ] Delete old records
- [ ] Filter historical data
- [ ] View error details
- [ ] Resize images for each provider

## Future Enhancements (Out of Scope)

### Phase 2 Features
- Batch processing: Upload multiple files at once
- A/B testing: Same document, different models, side-by-side
- Statistical dashboard: Success rates, avg time, cost tracking
- Schema versioning: Track schema evolution over time
- API key rotation: UI to manage keys without restart

### Phase 3 Features
- Custom provider plugins: Add new VLM providers dynamically
- Model fine-tuning: Use extracted data to fine-tune models
- Workflow automation: Predefined processing pipelines
- Advanced filtering: Regex search on results, semantic search
- Cloud deployment option: Optional auth for remote access

## Documentation Plan

### User Documentation
1. **README.md**: Setup, quick start, features overview
2. **SCHEMAS.md**: How to write Pydantic schemas, examples
3. **PROVIDERS.md**: Provider-specific configuration, API keys
4. **TROUBLESHOOTING.md**: Common issues and solutions

### Developer Documentation
1. **ARCHITECTURE.md**: System architecture, design decisions
2. **API.md**: REST API documentation
3. **CONTRIBUTING.md**: Development setup, coding standards

## Success Criteria

**Functional Requirements:**
- ✅ Upload and process all supported file types
- ✅ Test all three VLM providers successfully
- ✅ Create/save/load custom schemas
- ✅ Process multi-page PDFs with merged results
- ✅ View and search historical data
- ✅ Export results to JSON/CSV
- ✅ Delete old records
- ✅ Comprehensive error logging

**Non-Functional Requirements:**
- ✅ Response time < 30s for single-page documents
- ✅ Response time < 2min for 10-page PDFs
- ✅ UI responsive and intuitive
- ✅ Docker container < 2GB final image
- ✅ No data loss on container restart (volume persistence)
- ✅ Clear error messages at every failure point

## Risks and Mitigations

### Risk 1: VLM API Changes
**Mitigation:** Abstract provider interfaces, version adapters, easy to update

### Risk 2: PDF Processing Complexity
**Mitigation:** Use mature libraries (pdf2image), handle edge cases gracefully

### Risk 3: Schema Validation Failures
**Mitigation:** Clear error messages, show validation details, allow retry

### Risk 4: SQLite Performance at Scale
**Mitigation:** Indexes, periodic VACUUM, consider PostgreSQL if needed later

### Risk 5: Docker Image Size
**Mitigation:** Multi-stage build, alpine variants, careful dependency selection

## Open Questions (Resolved)

✅ **Schema templates**: Include built-in templates + custom user schemas
✅ **Multi-page PDFs**: Process all pages, merge into array results
✅ **Rate limiting**: Not needed for personal use
✅ **Schema persistence**: Dedicated database table with CRUD
✅ **Result comparison**: No side-by-side, export functionality instead
✅ **Docker volumes**: Yes, persistent volume for SQLite database
✅ **Model parameters**: Expose all provider-specific parameters
✅ **Image resizing**: Resize to optimal dimensions per provider (no enhancement)
✅ **Data deletion**: UI to delete old records

---

**Document Status:** Final Design
**Last Updated:** 2025-01-15
**Next Phase:** Implementation (see implementation.md)
