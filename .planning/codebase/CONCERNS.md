# Codebase Concerns

## Overview
This document identifies technical debt, bugs, security issues, performance concerns, and fragile areas in the OCR Platform codebase. Each concern includes specific file locations and recommendations.

---

## Security Concerns

### 1. Wide-Open CORS Configuration
**Category**: Security
**Severity**: High
**File**: `backend/main.py:9-15`

**Issue**:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Accepts requests from ANY origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why It's a Problem**:
- Any website can make requests to your API
- Combined with `allow_credentials=True`, this is a security risk
- No origin validation or allowlist

**Recommendation**:
- Restrict to specific origins: `allow_origins=["http://localhost:5173", "https://yourdomain.com"]`
- Remove `allow_credentials=True` if not needed
- Use environment variables for origin list

---

### 2. No Authentication/Authorization
**Category**: Security
**Severity**: High
**Files**: All `backend/routers/*.py`

**Issue**: No authentication layer exists. Anyone with API access can:
- Upload files
- Submit jobs (costing money)
- View all job history
- Delete jobs
- Modify schemas

**Recommendation**:
- Implement API key authentication
- Add user sessions (HTTP-only cookies or JWT)
- Add rate limiting per user
- Consider admin vs user roles

---

### 3. API Keys in Environment Variables (Plaintext)
**Category**: Security
**Severity**: Medium
**Files**: `backend/config.py:4-7`

**Issue**:
```python
class Settings(BaseSettings):
    nebius_api_key: str = ""
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
```

API keys are loaded from `.env` file in plaintext. If the file is compromised or committed to git, keys are exposed.

**Recommendation**:
- Add `.env` to `.gitignore` (already done)
- Use secret management service in production (AWS Secrets Manager, HashiCorp Vault)
- Rotate keys regularly
- Document key rotation procedure

---

### 4. No Input Sanitization Beyond Type Validation
**Category**: Security
**Severity**: Medium
**Files**: `backend/routers/upload.py`, `backend/services/processing.py`

**Issue**: Uploaded files are validated only for size and type. No content scanning for:
- Malicious files (ZIP bombs, polyglot files)
- Executable content disguised as images/PDFs
- Path traversal attacks in filenames

**Recommendation**:
- Validate file content (magic bytes), not just extension
- Sanitize filenames (remove `../`, special chars)
- Scan with clamav or similar
- Limit file dimensions (images) and page count (PDFs)

---

### 5. Unused PaddleOCR Dependencies Exposed in Code
**Category**: Security/Maintenance
**Severity**: Low
**File**: `backend/pyproject.toml:20-23`

**Issue**:
```python
# Note: PaddlePaddle/PaddleOCR temporarily removed due to ARM64 compatibility issues
# These will be re-added in Phase 2 when hybrid pipeline is implemented
# "paddlepaddle>=3.3.0",
# "paddleocr>=3.3.3",
```

PaddleOCR code exists in `backend/services/paddle_ocr_service.py` but is not packaged. This creates confusion about what's actually installed.

**Recommendation**:
- Either remove the service file or add proper feature flag detection
- Document why it's disabled
- Add try/except ImportError with clear error message if someone tries to use it

---

## Performance Concerns

### 6. No Connection Pooling for Database
**Category**: Performance
**Severity**: Medium
**File**: `backend/database/crud.py` (throughout)

**Issue**: Each database function creates a new connection:
```python
async def get_job(job_id: int):
    async with aiosqlite.connect(DB_PATH) as db:  # New connection each time
```

SQLite has limits on concurrent connections. This could cause bottlenecks under load.

**Recommendation**:
- Use a connection pool
- Or use a singleton connection with proper locking
- Profile connection overhead under load

---

### 7. Synchronous File I/O in Async Functions
**Category**: Performance
**Severity**: Low
**Files**: `backend/services/image_service.py`, `backend/services/paddle_ocr_service.py`

**Issue**: Image operations (PIL) are synchronous:
```python
image = Image.open(image_path)  # Blocking I/O
image.save(buffer, format=format)
```

In async handlers, blocking I/O can block the entire event loop.

**Recommendation**:
- Run file I/O in thread pool: `await loop.run_in_executor(None, func)`
- Or use aiofiles for async file operations
- Profile to see if this is actually a bottleneck

---

### 8. No Rate Limiting
**Category**: Performance
**Severity**: Medium
**Files**: All API endpoints

**Issue**: No rate limits on:
- File uploads
- Job submissions
- API calls to providers

A single user could:
- Upload unlimited files (fill disk)
- Submit unlimited jobs (drain API credits)
- DDoS the providers

**Recommendation**:
- Add rate limiting middleware (slowapi, limiter)
- Per-IP and per-user limits
- Queue system for jobs (don't process all simultaneously)

---

### 9. Frontend Polling Inefficiency
**Category**: Performance
**Severity**: Low
**File**: `frontend/src/pages/BaseExtractionPage.tsx` (and other pages)

**Issue**: Frontend polls job status every 2 seconds continuously:
```typescript
useEffect(() => {
  const interval = setInterval(() => {
    fetchJobStatus(jobId);
  }, 2000);
  return () => clearInterval(interval);
}, [jobId]);
```

This creates unnecessary load even after job completes.

**Recommendation**:
- Use exponential backoff (2s → 4s → 8s)
- Stop polling when job is success/error
- Consider WebSocket for real-time updates

---

## Tech Debt

### 10. Duplicate JSON Import Statements
**Category**: Tech Debt
**Severity**: Low
**File**: `backend/services/processing.py:95-96`

**Issue**:
```python
import json
import json  # Duplicate import on next line
```

**Why It's a Problem**:
- Cluttered code
- Suggests incomplete refactoring

**Recommendation**: Remove duplicate import

---

### 11. Inconsistent Error Handling
**Category**: Tech Debt
**Severity**: Medium
**Files**: Throughout `backend/routers/` and `backend/services/`

**Issue**: Some functions return error dicts, others raise exceptions, some do both:
```python
# In processing.py:85-89
if "error" in result:
    return {
        "success": False,
        "error": f"Provider error: {result['error']}",
        "raw_response": result
    }

# In routers/processing.py:31-32
raise HTTPException(status_code=404, detail="Schema not found")
```

**Why It's a Problem**:
- Callers don't know what to expect
- Inconsistent error responses to clients

**Recommendation**:
- Choose one pattern (exceptions recommended)
- Document error handling approach
- Use error response middleware for consistent API errors

---

### 12. Bare `except` Clauses Swallow Errors
**Category**: Tech Debt/Bug
**Severity**: Medium
**File**: `backend/routers/processing.py:119-122`

**Issue**:
```python
try:
    await crud.update_job_metadata(job_id, classification_info)
except:
    pass  # Metadata update is optional
```

**Why It's a Problem**:
- Swallows ALL errors, including programming errors
- Makes debugging impossible
- Silent failures

**Recommendation**:
```python
try:
    await crud.update_job_metadata(job_id, classification_info)
except AttributeError:
    pass  # Only catch expected errors
```

---

### 13. TODO in Production Code
**Category**: Tech Debt
**Severity**: Low
**File**: `backend/services/paddle_ocr_service.py:252`

**Issue**:
```python
# TODO: Integrate dedicated table extraction library
```

**Why It's a Problem**:
- Unimplemented feature referenced in code
- PaddleOCR returns empty list for tables

**Recommendation**:
- Either implement or remove the TODO
- Document why table extraction is not available
- Return NotImplementedError with clear message

---

### 14. No Database Migration System
**Category**: Tech Debt
**Severity**: Medium
**File**: `backend/database/migrations.py`

**Issue**: Database schema is created with a single script:
```python
async def init_db():
    await db.execute("""CREATE TABLE IF NOT EXISTS schemas...""")
```

No versioning, no rollback, no incremental migrations.

**Why It's a Problem**:
- Can't evolve schema safely
- No way to rollback changes
- Difficult to deploy schema changes

**Recommendation**:
- Use Alembic for database migrations
- Version all schema changes
- Add migration to deployment process

---

## Bugs

### 15. Unused `extraction_method` Parameter
**Category**: Bug
**Severity**: Low
**File**: `backend/routers/processing.py:17`

**Issue**:
```python
async def process_document(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    extraction_method: str = None  # Never passed from client
):
```

The function signature has `extraction_method` but the actual value comes from `request.extraction_method`. This parameter is never used.

**Recommendation**: Remove unused parameter

---

### 16. Inconsistent Job Status Endpoints
**Category**: Bug
**Severity**: Medium
**Files**: `frontend/src/lib/api.ts:121-138`

**Issue**:
```typescript
export async function getJobStatus(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/process/status/${jobId}`);  // /api/process/status/:id
  // ...
}

export async function pollJobStatus(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE}/text/status/${jobId}`);  // /api/text/status/:id
  // ...
}
```

Two different status endpoints (`/process/status/` vs `/text/status/`) but similar purpose. The `pollJobStatus` function might not work for vision jobs.

**Recommendation**:
- Unify to single `/api/jobs/{id}` endpoint (already exists)
- Remove redundant status endpoints
- Update frontend to use `/api/jobs/{id}`

---

### 17. Missing Database Connection Close
**Category**: Bug
**Severity**: Low
**File**: `backend/database/crud.py` (throughout)

**Issue**: While `async with` is used, there's no guarantee connections close on error:
```python
async def get_job(job_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # If exception here, connection might not close properly
```

**Recommendation**:
- Add explicit cleanup in finally blocks
- Or use connection pool with timeout

---

## Fragile Areas

### 18. No Retry Logic for VLM API Calls
**Category**: Fragile
**Severity**: Medium
**Files**: `backend/services/nebius.py`, `backend/services/openrouter.py`, `backend/services/gemini.py`

**Issue**: If VLM API call fails due to transient error (network blip, rate limit), job immediately fails:
```python
result = await provider.process_image(...)  # No retry on failure
if "error" in result:
    return {"success": False, "error": ...}
```

**Recommendation**:
- Implement exponential backoff retry
- Retry on specific errors (503, 429, timeout)
- Max retry limit (3-5 attempts)

---

### 19. No Job Queue or Worker Pool
**Category**: Fragile
**Severity**: High
**File**: `backend/routers/processing.py:126-128`

**Issue**:
```python
background_tasks.add_task(run_processing_job, job_id, str(file_path))
```

Background tasks run in FastAPI's event loop. If many jobs submit simultaneously:
- All jobs run concurrently
- No resource limits
- Could exhaust memory/API rate limits

**Recommendation**:
- Implement job queue (Celery, RQ, or custom)
- Worker pool with max concurrency
- Job prioritization

---

### 20. Duplicate Import Statement
**Category**: Fragile/Tech Debt
**Severity**: Low
**File**: `backend/services/processing.py:95-96`

**Issue**:
```python
import json
import json
```

This duplicate import could cause confusion and suggests incomplete refactoring.

**Recommendation**: Remove duplicate line

---

### 21. Hardcoded Paths in Multiple Locations
**Category**: Fragile
**Severity**: Medium
**Files**: `backend/main.py:32-35`, `backend/config.py:14`

**Issue**:
```python
# main.py
static_dir = "/app/frontend/dist"
if not os.path.exists(static_dir):
    static_dir = "../frontend/dist"

# config.py
database_url: str = "sqlite:///./data/ocr_platform.db"
```

Paths are hardcoded relative to execution directory. Breaks if run from different location.

**Recommendation**:
- Use `pathlib.Path` with `__file__` for relative paths
- Make all paths configurable via environment
- Document expected working directory

---

### 22. No Graceful Shutdown
**Category**: Fragile
**Severity**: Medium
**File**: `backend/main.py`

**Issue**: No graceful shutdown handlers. If server receives SIGTERM:
- In-progress jobs are killed
- Database connections may corrupt
- File uploads may be incomplete

**Recommendation**:
- Add shutdown event handler
- Wait for in-progress jobs to complete
- Close database connections properly
- Implement health check for load balancers

---

## Testing Gaps

### 23. No Frontend Tests
**Category**: Quality
**Severity**: Medium
**Files**: All `frontend/src/**/*.tsx`

**Issue**: Zero frontend automated tests. All testing is manual.

**Recommendation**:
- Add Vitest + React Testing Library
- Test critical components (FileUpload, SchemaEditor)
- Test API integration (MSW for mocking)

---

### 24. Limited Backend Test Coverage
**Category**: Quality
**Severity**: Medium
**Files**: `backend/tests/`

**Issue**:
- No tests for VLM providers (nebius, openrouter, gemini)
- No tests for document classifier
- No tests for text extraction service
- No tests for routers (upload, schemas, jobs)

**Recommendation**:
- Add unit tests for each service
- Mock external API calls
- Increase coverage to >80%

---

### 25. Tests Use Real API Calls
**Category**: Quality/Cost
**Severity**: Medium
**File**: `backend/tests/test_integration.py`

**Issue**: Integration tests make real API calls to VLM providers. This:
- Costs money per test run
- Makes tests slow (3-30 seconds per test)
- Requires valid API keys to run tests

**Recommendation**:
- Mock VLM provider responses
- Use fixtures for common API responses
- Only make real API calls in manual smoke tests

---

## Documentation Issues

### 26. Incomplete API Documentation
**Category**: Documentation
**Severity**: Low
**Files**: `backend/routers/*.py`

**Issue**: Some endpoints lack detailed docstrings. Example from `processing.py:19-26`:
```python
"""
Process a document with intelligent routing

extraction_method options:
- None or "auto": Automatically detect best pipeline (recommended)
- "text": Force text extraction (pdfplumber + LLM) - fast & cheap
- "vision": Force vision extraction (VLM) - accurate & expensive
"""
```

But request/response types are not documented in the docstring (only in Pydantic models).

**Recommendation**:
- Add examples to docstrings
- Document error responses
- Add usage examples to OpenAPI docs via FastAPI decorators

---

### 27. No Architecture Decision Records (ADRs)
**Category**: Documentation
**Severity**: Low
**Project Root**: No `docs/architecture/decisions/` directory

**Issue**: Design decisions are not documented:
- Why FastAPI over Flask/Django?
- Why SQLite over PostgreSQL?
- Why polling instead of WebSockets?
- Why VLM approach over traditional OCR?

**Recommendation**:
- Create ADRs for major decisions
- Document trade-offs considered
- Record alternatives rejected and why

---

## Summary by Severity

### High Priority
1. Wide-open CORS (`backend/main.py:9-15`)
2. No authentication (all routers)
3. No job queue/workers (`backend/routers/processing.py:126-128`)

### Medium Priority
4. No connection pooling (`backend/database/crud.py`)
5. No rate limiting (all endpoints)
6. Inconsistent error handling (backend-wide)
7. No database migrations (`backend/database/migrations.py`)
8. Bare except clauses (`backend/routers/processing.py:119-122`)

### Low Priority
9. Duplicate imports (`backend/services/processing.py:95-96`)
10. TODO in code (`backend/services/paddle_ocr_service.py:252`)
11. No graceful shutdown (`backend/main.py`)
12. Hardcoded paths (`backend/main.py:32-35`)

---

## Recommended Action Order

1. **Fix CORS and add auth** (Security)
2. **Add job queue** (Scalability)
3. **Implement rate limiting** (Performance & Security)
4. **Add retry logic** (Reliability)
5. **Standardize error handling** (Maintainability)
6. **Add database migrations** (Deployment safety)
7. **Improve test coverage** (Quality)
8. **Add graceful shutdown** (Production readiness)
