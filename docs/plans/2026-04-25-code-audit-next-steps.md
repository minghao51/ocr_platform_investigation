# Code Audit: Next Steps

> Created: 2026-04-25
> Status: Priority-ordered action items from codebase audit
> Confidence: High (findings based on direct code review)

## Audit Summary

**Overall Health Rating: Moderate**

| Category | Rating |
|----------|--------|
| Code Quality | Good |
| Security | Moderate |
| Architecture | Good |
| Performance | Moderate |
| Testing | Good |
| Documentation | Moderate |

**Top 5 Critical Findings:**
1. No background job retry/failure recovery (fire-and-forget tasks)
2. JWT secret defaults to placeholder string
3. No error tracking/monitoring in production
4. Missing database indexes for analytics queries
5. SQLite async concurrency limitations

---

## Week 1: Quick Wins (Low Effort, High Impact)

### 1. Add Database Indexes
**Severity:** High | **Type:** Performance

Add indexes to prevent analytics query degradation at scale.

```sql
-- backend/database/migrations.py
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON processing_jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON processing_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_provider ON processing_jobs(provider, model);
CREATE INDEX IF NOT EXISTS idx_corrections_job ON job_corrections(job_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_results_run ON benchmark_results(run_id);
```

**Files to modify:** `backend/database/migrations.py`

---

### 2. Fail Fast on Default JWT Secret
**Severity:** Critical | **Type:** Security

Prevent insecure default from silently being used in production.

```python
# backend/config.py
@model_validator(mode="after")
def validate_jwt_secret(self):
    default_secret = "change-me-in-production-use-openssl-rand-hex-32"
    if self.jwt_secret_key == default_secret:
        import os
        if os.environ.get("ENVIRONMENT") == "production":
            raise ValueError("JWT secret must be changed from default in production")
    return self
```

**Files to modify:** `backend/config.py`

---

### 3. Replace print() with Proper Logging
**Severity:** Medium | **Type:** Observability

Multiple locations use `print()` instead of structured logging.

**Files to modify:**
- `backend/services/processing.py:917, 1013, 1166`
- `backend/services/processing.py:975` (`print()` for success)

```python
# Before
print(f"ERROR processing job {job_id}: {error_details}")
print(f"Traceback: {traceback.format_exc()}")

# After
logger.error(f"Job {job_id} failed: {error_details}", exc_info=True)
```

---

## Week 2: Structural Improvements

### 4. Implement Job Timeout/Heartbeat
**Severity:** Critical | **Type:** Architecture

Jobs stuck in "processing" forever have no recovery mechanism.

**Approach:**
- Add `started_at` timestamp when job transitions to "processing"
- Add a cleanup task (cron or background loop) that:
  - Finds jobs stuck in "processing" for > 15 minutes
  - Updates them to "error" with message "Job timed out after processing failure"
  - Optionally: implements retry logic (max 2 retries)

**Files to modify:** `backend/database/crud.py`, `backend/services/processing.py`

---

### 5. Add Request ID to Logs
**Severity:** Medium | **Type:** Observability

Enable request tracing through logs.

**Implementation:**
```python
# backend/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        
        # Add to logging
        logging.setLogRecordFactory(
            lambda record: setattr(record, 'request_id', request_id) or record
        )
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

**Files to add:** `backend/middleware.py`
**Files to modify:** `backend/main.py`

---

### 6. Move Quality Gate Thresholds to Config
**Severity:** Medium | **Type:** Configuration

Hardcoded thresholds in `quality_gate.py` should be environment-configurable.

**Files to modify:** `backend/config.py`, `backend/services/quality_gate.py`

---

## Week 3-4: Process & Tooling

### 7. Add Pre-commit Hooks
**Severity:** Medium | **Type:** Process

Prevent code style drift before it reaches code review.

**Add to `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
      - id: ruff format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all-your-deps]
```

**Files to add:** `.pre-commit-config.yaml`
**Files to modify:** `pyproject.toml` (if not exists)

---

### 8. Integrate Error Tracking (Sentry)
**Severity:** High | **Type:** Operations

Production errors are currently invisible.

**Installation:**
```python
# backend/main.py
import sentry_sdk
from sentry_sdk.integrations.starlette import StarletteIntegration

sentry_sdk.init(
    dsn=get_settings().sentry_dsn,
    integrations=[StarletteIntegration()],
    environment=settings.environment,
)
```

**Files to modify:** `backend/main.py`, `backend/config.py`
**Note:** Requires Sentry account and DSN configuration

---

### 9. Add Database Migration Tests
**Severity:** Medium | **Type:** Testing

Prevent schema drift in CI/CD.

**Implementation:**
```python
# backend/tests/unit/test_migrations.py
def test_migrations_preserve_data():
    """Test that migrations don't corrupt existing data."""
    # Create test DB, apply migrations, verify schema
    # Then add a new migration, re-apply, verify data intact
```

**Files to add:** `backend/tests/unit/test_migrations.py`

---

### 10. Add API Versioning Infrastructure
**Severity:** Low | **Type:** Architecture

Prepare for future API evolution without breaking changes.

**Approach:**
- Prefix all routes with `/api/v1/`
- Add `API_VERSION = "v1"` to config
- Document versioning strategy in README

**Files to modify:** All routers, `backend/main.py`

---

## Not Prioritized (Future Considerations)

| Item | Reason |
|------|--------|
| Switch to PostgreSQL | SQLite concurrency limits - defer until scaling proves necessary |
| Add rate limiting to WebSocket | DoS vector - lower priority for internal tool |
| GraphQL migration | REST API adequate for current scope |
| WebSocket authentication | Currently relies on guest token header |

---

## Findings Detail (Reference)

### Critical
- **Background job reliability** - Fire-and-forget tasks with no retry
- **JWT secret default** - `config.py:36` - Insecure fallback

### High
- **No error tracking** - No Sentry or equivalent
- **Missing indexes** - Analytics queries will degrade
- **SQLite concurrency** - `database is locked` errors under load

### Medium
- **Race condition potential** - File access check then disk check
- **Inconsistent error handling** - `print()` vs `logger.error()`
- **No request ID** - Impossible to trace requests
- **Hardcoded thresholds** - Quality gate not configurable

### Low
- **Schema JSON parsing** - Could fail if already dict
- **No API versioning** - Future breaking changes
- **No Swagger docs** - Developer experience
