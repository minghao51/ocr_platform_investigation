# State — OCR Platform

Last updated: 2026-05-12

---

## 1. Feature Implementation Status

| Feature | Backend | Frontend | Notes |
|---------|---------|----------|-------|
| File upload (streaming, validation) | Full | Full | `routers/upload.py`, `components/FileUpload.tsx` |
| PDF text-layer analysis | Full | Full | `routers/upload.py:121`, auto-triggered in `MethodModelSelector.tsx:53` |
| **Extraction Methods** | | | 6 methods defined; see below |
| Auto-detection (DocumentClassifier) | Full | Full | `services/document_classifier.py`, routing in `routers/processing.py:96-138` |
| Text extraction (pdfplumber + LLM) | Full | Full | `services/processors/text.py`, `services/text_extraction.py` |
| Vision extraction (VLM) | Full | Full | `services/processors/vision.py` |
| Hybrid extraction (text + vision) | Full | Full | `services/hybrid_processing.py` |
| Docling parse (PyMuPDF → LLM) | Full | Full | `services/processors/docling_parse.py` |
| Docling extract (local VLM) | Full | Full | `services/processors/docling_extract.py` |
| Transcription (document → Markdown) | Full | Full | `services/transcription_service.py` |
| **Schemas** | | | |
| CRUD | Full | Full | `routers/schemas.py`, `components/SchemaEditor.tsx` |
| AI schema suggestion | Full | Full | `services/schema_suggester.py` |
| Built-in templates (Invoice, Receipt, ID, Generic) | Full | Full | `services/schema_service.py:55` |
| Schema suggestion history | Full | Full | `routers/schemas.py:184` |
| Schema DELETE endpoint | **Missing** | **Missing** | No delete route exists |
| **Processing Pipeline** | | | |
| Job queue (durable, async worker) | Full | N/A | `services/job_queue.py` |
| Recovery of in-flight jobs on restart | Full | N/A | `services/job_queue.py:106` |
| Prompt optimizer | Full | N/A | `services/prompt_optimizer.py` |
| Prompt learning from corrections | Full | N/A | `services/prompt_learning.py` |
| Chunking for large documents | Full | N/A | `services/chunking_service.py`, used in `docling_parse.py:85` |
| **Quality Gate** | | | |
| Pre-processing quality check (blur/skew/noise/contrast/brightness/resolution) | Full | Partial | `services/quality_gate.py` — QualityBadge exists but only shown for images on ProcessingPage |
| Image preprocessing (deskew, denoise, CLAHE, binarize, normalize) | Full | N/A | `services/image_preprocessor.py` |
| Quality check endpoint (by file_id) | Full | Full | `routers/quality.py:46` |
| Quality check with upload | Full | Full | `routers/quality.py:90` |
| **Auth** | | | |
| JWT login/password (argon2) | Full | Full | `routers/auth.py`, `auth.py` |
| Token version revocation (logout) | Full | N/A | `routers/auth.py:80` |
| Guest tokens for unauthenticated upload | Full | Full | `routers/upload.py:33`, `components/LoginPanel.tsx` |
| Demo daily request limits | Full | N/A | `dependencies.py:118` |
| Rate limiting (slowapi) | Full | Partial | `limiter.py` — frontend shows alert but no per-endpoint throttling UI |
| Admin-only routes (analytics, benchmarks) | Full | Partial | Endpoints exist, frontend shows them to all users (empty data for non-admin) |
| **WebSocket** | | | |
| Ticket-based WebSocket auth | Full | Full | `routers/websocket.py:27` exchanges JWT for short-lived ticket |
| Real-time job status broadcast | Full | Full | `routers/websocket.py:109`, `lib/websocket.ts` |
| Reconnection with exponential backoff | N/A | Full | `lib/websocket.ts:83` |
| Fallback to polling | Full | Full | `BaseExtractionPage.tsx:347` |
| **Jobs** | | | |
| List with pagination/filters | Full | Full | `routers/jobs.py:92`, `pages/HistoryPage.tsx` |
| Get/delete individual jobs | Full | Full | `routers/jobs.py:112,123` |
| Corrections (diff, review, save) | Full | Full | `routers/jobs.py:149`, `components/CorrectionReviewPanel.tsx` |
| **Benchmarks** | | | |
| CRUD for runs + results | Full | Full | `routers/benchmarks.py`, `benchmarks/runner.py` |
| Model comparison | Full | Full | `routers/benchmarks.py:53` |
| Benchmark CLI | Full | N/A | `cli.py` |
| **Analytics** | | | |
| Usage analytics endpoint | Full | Partial | `routers/analytics.py` — data shown on BenchmarksPage, no dedicated page |
| Correction pattern analysis | Full | Full | `database/crud/benchmarks.py:283` |
| Production correction rate | Full | Full | `database/crud/benchmarks.py:330` |

---

## 2. Stubbed / Unimplemented

### Endpoints with no frontend routes
- `/api/admin` — no admin dashboard page exists
- Schema DELETE — no endpoint (`routers/schemas.py` only has GET, POST)
- File DELETE —  no endpoint to delete uploaded files

### `close_pool` is a no-op
`database/pool.py:52` — "No-op for compatibility — included for future pool implementation." The `main.py:52` calls it on shutdown but it does nothing.

### PaddleOCR referenced but not integrated
`frontend/src/pages/MethodologyPage.tsx:547` — "Hybrid Pipeline" table says "Tool: PaddleOCR + VLM" but no PaddleOCR code exists in the codebase.

### Copy-paste vs structured extraction classification
`services/document_classifier.py:255` — For "mixed" documents with complexity > 70, the classifier suggests "vision" not "hybrid" or "docling-parse". The chosen method may not match the methodology page's claim.

### Unused schema_mode 'raw' with transcription
`backend/models/schemas.py:31` — `schema_mode` supports "raw", "auto-detect", "manual" but "raw" only works with `docling-parse`. No guard prevents sending "raw" with other methods (the check is in `routers/processing.py:179` but returns a 400, not a client-side prevention).

---

## 3. Known Bugs

### B-1: Unused `page_quality_reports` list in VisionProcessor
`services/processors/vision.py:165` — The `page_quality_reports` list is populated per-page but only `page_quality_reports[0]` is used (line 237). Line 221-229 computes `avg_score` from ALL reports but then only passes the first report's checks to `update_quality_info`. The avg_score is passed to `quality_score` but the quality_checks dict is only from page 0.

```python
# line 237
"quality_report": self.quality_gate.to_dict(page_quality_reports[0])  # Only first page!
```

### B-2: Silent error swallows via bare `pass`
Multiple locations silently swallow exceptions:

- `services/processing_utils.py:25` — `json.JSONDecodeError` inside `parse_and_validate_response` when `data` is str, silently passed
- `services/processors/vision.py:189` — JSON decode error for `preprocessing_applied` silently passed
- `services/hybrid_processing.py:28` — JSON decode error in `_parse_and_validate_response` silently passed
- `database/crud/jobs.py:179` — JSON decode error merging metadata silently passed
- `benchmarks/datasets.py:74,81,88,95,117,122` — Six bare `pass` statements in fixture generation
- `services/chunking_service.py:225` — Dict merge conflict silently passed

### B-3: `max_tokens` inconsistency between provider defaults and job config
`services/processing.py:173` — Default `max_tokens` is 8192, but:
- `services/openrouter.py:59` — Defaults to 4096 in `process_image` payload
- `services/openrouter.py:134` — Defaults to 4096 in `process_text` signature
- `services/gemini.py:41` — Defaults to 4096

This means the 8192 default set in `run_processing_job` is silently capped to 4096 at the provider level.

### B-4: `list_jobs` parameter type mismatch
`routers/jobs.py:95` — `provider: str = None` is typed as `str` but default is `None`. Should be `Optional[str]`.

### B-5: Rate limiter bypass for `get_optional_user` paths
`routers/processing.py:33` — `@limiter.limit` decorator is applied, but `get_optional_user` on line 40 doesn't always authenticate. `limiter.py:35` checks `user.get("is_admin", False)` for exemption. If the token is invalid, `_get_request_user` (line 22) catches the exception and returns `None`, so the rate limit still applies — but the error message is confusing when the token is actually invalid.

### B-6: CORS with `allow_credentials=False`
`backend/main.py:78` — `allow_credentials=False` prevents cookies from being sent cross-origin. If the frontend ever switches from localStorage to httpOnly cookies for auth, this will break.

### B-7: `analyze_pdf` imports `fitz` at runtime, not top-level
`routers/upload.py:142` — `import fitz` is inside the handler. If PyMuPDF is not installed, this returns a 500 with "PDF analysis not available" rather than failing at startup.

---

## 4. Security Concerns

### S-1: Default JWT secret in source (High)
`backend/config.py:8` — `_DEFAULT_JWT_SECRET = "change-me-in-production-use-openssl-rand-hex-32"`. The code correctly raises `RuntimeError` in non-local environments (`config.py:81-84`), but the secret is visible in source and could be used by anyone who inspects the code.

### S-2: Gemini API key exposed in URL query parameter (Medium)
`backend/services/gemini.py:52` — `f"{self.BASE_URL}/models/{model}:generateContent?key={self.api_key}"`. API keys in URL query parameters can leak via:
- Server access logs
- HTTP referrer headers
- Browser history (if debugging locally)
- Network monitoring tools

OpenRouter does not have this issue (uses `Authorization: Bearer` header).

### S-3: JWT access tokens in localStorage (Medium)
`frontend/src/lib/api/client.ts:19,47` — JWT tokens are stored in `localStorage`. This is standard but makes tokens accessible to any JavaScript running on the same origin (XSS vulnerability). No `httpOnly` cookie option exists.

### S-4: No CSRF protection (Low)
All API endpoints use `Bearer` token auth. No CSRF tokens are implemented. Mitigated by `allow_credentials=False` in CORS, but first-party CSRF is possible if an attacker can execute script on the same origin.

### S-5: SQL injection via f-string in migrations (Low)
`backend/database/migrations.py:20` — `f"PRAGMA table_info({table})"` uses f-string substitution for the table name. While table names are hardcoded constants, this is a risky pattern.
`backend/database/crud/benchmarks.py:127,145,211,229,245,266` — `_SUCCESS_RATE_SQL` is injected via f-string into SQL queries. Since it's a constant string, risk is low, but the pattern is fragile.

### S-6: Broad exception handlers (Medium)
70+ `except Exception` handlers across the codebase. Most notable:
- `services/openrouter.py:193` — returns `{"error": str(e)}` on any exception, which is acceptable
- `services/gemini.py:354` — same pattern
- `services/schema_service.py:40` — returns validation failure for any exception type, masking errors
- `routers/schemas.py:114` — catches broad `Exception` for UNIQUE constraint, could mask other errors

### S-7: `has_api_key` leaks provider configuration state
`backend/services/provider_catalog.py:44` — The frontend receives a boolean `has_api_key` per provider. While not the key itself, this reveals which providers a deployment has configured.

---

## 5. Performance Issues

### P-1: No connection pooling (High)
`database/pool.py:40` — `connect()` creates a new `aiosqlite.Connection` on every call and closes it after each operation. Every CRUD operation (and there can be many per request) opens/closes a connection. The comment "included for future pool implementation" indicates this is known tech debt.

Each upload triggers at least: DB INSERT for file record → SELECT for get_uploaded_file → DB INSERT for job → job queue worker chain (SELECT → UPDATE → UPDATE → another SELECT). That's 6+ separate connections per job.

### P-2: Benchmark queries fetch all rows, filter in Python (Medium)
`routers/benchmarks.py:62,103` — `list_benchmark_runs(limit=500)` fetches up to 500 rows, then filters in Python:
```python
dataset_runs = [r for r in runs if r.get("overall_accuracy") is not None]
```
The `dataset` filter should be pushed to SQL.

### P-3: Analytics queries run 5+ separate SQL queries (Medium)
`database/crud/benchmarks.py:173` — `get_job_analytics` runs:
1. Overview query
2. Pipeline distribution query
3. Provider breakdown query
4. Daily trend query
5. Correction patterns query
6. Benchmark accuracy query

Each is a separate database round-trip. The filter params (`where_sql`) are duplicated across all queries. Could use a single CTE or materialized view.

### P-4: No file size limit for PDF-to-image conversion (Medium)
`services/processors/vision.py:159` — `image_service.pdf_to_images(pdf_path)` converts ALL pages of a PDF to images with no page limit. A 100+ page PDF would create 100+ PIL Image objects in memory simultaneously.

### P-5: `list_benchmark_runs(limit=500)` repeated on page load (Low)
`frontend/src/pages/BenchmarksPage.tsx:28` — Three parallel API calls (`loadComparison`, `loadRuns`, `loadAnalytics`) each hit the backend. No caching layer between requests.

---

## 6. Maintenance Issues

### M-1: Extraction method list duplicated in 6+ locations (High)
Changing the set of extraction methods requires updating:
1. `backend/routers/processing.py:141` — validation list
2. `backend/routers/extract_settings.py:8` — metadata & descriptions
3. `backend/models/schemas.py:35` — `Literal` type in `ProcessRequest`
4. `backend/models/schemas.py:36` — `Literal` type union
5. `frontend/src/lib/methods.ts:21` — `ALL_METHODS` + method metadata
6. `frontend/src/lib/api/types.ts:53` — `Job.processing_method` union
7. `frontend/src/lib/api/types.ts:116` — `ProcessRequest.extraction_method` union

A shared source of truth (YAML config or backend endpoint) would reduce drift risk.

### M-2: Provider class map duplicated in 5 services (High)
The dictionary `{"openrouter": OpenRouterProvider, "gemini": GeminiProvider, "litellm": LiteLLMProvider}` is repeated in:
- `services/processing.py:25`
- `services/processors/factory.py:71` (`_HybridProcessor`)
- `services/processors/docling_parse.py:363`
- `services/processors/vision.py:262`
- `services/processors/text.py:43`
- `services/schema_suggester.py:15`

Adding a new provider requires updating all 6 locations.

### M-3: Circular-import workaround via inline imports (Medium)
Multiple services use inline `import` statements inside methods to avoid circular imports:
- `services/processing.py:70` — `from pathlib import Path`
- `services/processors/docling_parse.py:352` — six inline imports inside `process()`
- `services/processors/vision.py:253` — same pattern
- `services/processors/text.py:22` — same pattern
- `services/processors/factory.py:62-65` — inside `_HybridProcessor.process()`

### M-4: `/api` hardcoded in frontend and backend (Medium)
`frontend/src/lib/api/client.ts:1` — `const API_BASE = '/api'`
`backend/routers/` — all routers use `prefix="/api/..."`

There's no configurable API base path. Running behind a reverse proxy with a different prefix requires changes in both frontend and backend.

### M-5: `app.state.rate_limit_user` cache (Low)
`limiter.py:14` — caches the user payload in `request.state.rate_limit_user`. If the token changes during a request (via middleware), the cached value is stale. Unlikely in practice but inconsistent.

### M-6: `_ = current_user` pattern fragile (Low)
Multiple routes use `_ = current_user` to suppress "unused variable" warnings:
- `routers/analytics.py:22`
- `routers/benchmarks.py:17,32,45,60,102`
- `routers/quality.py:111`

If the auth dependency changes, these won't break loudly but access control may silently degrade.

### M-7: Mixed string formatting styles (Low)
The codebase uses three styles inconsistently:
- `%`-formatting: `logger.warning("Job %s failed: %s", job_id, error_details)` — 15+ log lines
- `.format()`: occasional usage
- f-strings: most new code
- Mix in the same file: `services/processing.py` has all three

### M-8: `production_correction_rate` naming mismatch (Low)
`database/crud/benchmarks.py:330` — The field is named `production_correction_rate` in the API response, but the frontend `UsageAnalytics` type in `frontend/src/lib/api/types.ts` uses `production_correction_rate`. This matching actually works, but the term "production" is confusing since there's no "production" vs "non-production" distinction in the data.

### M-9: `settings.ts` `_settingsCache` not invalidated on auth change (Low)
`frontend/src/lib/api/settings.ts:20` — `_settingsCache` is cached indefinitely. If provider configuration changes or API keys are updated, the frontend needs a page reload. `clearExtractSettingsCache()` is exported but never called.

### M-10: No `package.json` scripts for linting (Low)
`frontend/` — Tailwind v4, Vite, and TypeScript are configured but no `lint` script is defined in package.json. Only `check` (TypeScript) and `test` exist.

### M-11: Variable shadowing in `gemini.py`
`backend/services/gemini.py:82` — `content = candidate["content"]` shadows the local variable `content` defined on line 37. This is error-prone:

```python
content: Dict[str, Any] = {  # line 37
    "contents": [{"parts": parts}],
    ...
}
# ... 45 lines later ...
content = candidate["content"]  # line 82 - shadows!
content_text = part["text"]     # uses different variable
```
