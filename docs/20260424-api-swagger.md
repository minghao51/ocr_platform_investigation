# OCR Platform API Documentation

**Base URL:** `/api`  
**Version:** 1.0.0  
**Authentication:** Bearer JWT token via `Authorization` header (where required)

---

## Table of Contents

- [Authentication](#authentication)
- [Upload](#upload)
- [Processing](#processing)
- [Schemas](#schemas)
- [Jobs](#jobs)
- [Providers](#providers)
- [Text Processing](#text-processing)
- [Quality Check](#quality-check)
- [Benchmarks](#benchmarks)
- [Analytics](#analytics)
- [WebSocket](#websocket)
- [Health](#health)
- [Common Parameters](#common-parameters)
- [Error Responses](#error-responses)

---

## Authentication

### POST `/api/auth/login`

Authenticate user and return JWT token.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | User's username |
| `password` | string | Yes | User's password |

**Response `200`:**

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT access token |
| `token_type` | string | Always `"bearer"` |
| `user` | object | User info |
| `user.id` | integer | User ID |
| `user.username` | string | Username |
| `user.is_admin` | boolean | Admin flag |

**Error `401`:** Invalid username or password.

---

### POST `/api/auth/verify`

Verify a JWT token and return user information.

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Response `200`:**

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | integer | User ID |
| `username` | string | Username |
| `is_admin` | boolean | Admin flag |

**Error `401`:** Missing, invalid, or expired token.

---

## Upload

### POST `/api/upload/`

Upload a file for processing. Supports authenticated and guest (unauthenticated) access.

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | No | `Bearer <token>` for authenticated users |
| `X-Guest-Token` | string | No | Guest token for unauthenticated users (auto-generated if absent) |

**Request Body:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | The file to upload |

**Allowed file types:**
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Documents: `.pdf`, `.docx`, `.pptx`, `.txt`, `.md`, `.html`
- Audio: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`

**Max file size:** 10 MB

**Rate limit:** 5 requests/minute

**Response `200`:**

| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string (UUID) | Unique file identifier |
| `file_name` | string | Original filename |
| `file_type` | string | One of: `image`, `pdf`, `audio`, `document` |
| `file_size` | integer | File size in bytes |
| `guest_token` | string | Included only for unauthenticated uploads |

**Errors:**
- `400` — Invalid file type
- `413` — File too large

---

### POST `/api/upload/analyze-pdf/{file_id}`

Quick PDF text-layer detection for frontend method auto-selection.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string (UUID) | Yes | Uploaded file ID |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | No | `Bearer <token>` |
| `X-Guest-Token` | string | No | Guest token |

**Response `200`:**

| Field | Type | Description |
|-------|------|-------------|
| `file_id` | string | File ID |
| `has_text_layer` | boolean | Whether the PDF contains extractable text |
| `text_chars` | integer | Total characters of text found |
| `suggested_methods` | string[] | List of suggested processing methods |

**Errors:**
- `400` — File is not a PDF
- `404` — File not found
- `500` — PDF analysis failed or not available

---

## Processing

### POST `/api/process/`

Process a document with intelligent routing. Starts a background job.

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | No | `Bearer <token>` |
| `X-Guest-Token` | string | No | Guest token |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `extraction_method` | string | No | Override extraction method: `"auto"`, `"text"`, `"vision"`, `"hybrid"`, `"docling-parse"`, `"docling-extract"`, `"transcription"` |

**Request Body:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file_id` | string | Yes | — | UUID of uploaded file |
| `provider` | string | No* | — | VLM provider name (required for most methods) |
| `model` | string | No* | — | VLM model name (required for most methods) |
| `schema_id` | integer | No | — | ID of saved schema (mutually exclusive with `schema_definition`) |
| `schema_definition` | object | No | — | Inline JSON schema definition |
| `schema_mode` | string | No | `"auto-detect"` | One of: `"raw"`, `"auto-detect"`, `"manual"` |
| `extraction_method` | string | No | `"auto"` | One of: `"auto"`, `"text"`, `"vision"`, `"hybrid"`, `"docling-parse"`, `"docling-extract"`, `"transcription"` |
| `prompt` | string | No | `"Extract all information from this document"` | Custom extraction prompt |
| `temperature` | float | No | `0.1` | LLM temperature |
| `max_tokens` | integer | No | `4096` | Max LLM output tokens |
| `quality_threshold` | float | No | `40.0` | Minimum quality score (0–100) |
| `auto_preprocess` | boolean | No | `true` | Auto-fix quality issues before VLM |
| `skip_quality` | boolean | No | `false` | Bypass quality gate entirely |

*Provider and model are required for `text`, `vision`, `hybrid`, and `transcription` methods. Not required for `docling-extract`.

**Rate limit:** 3 requests/minute

**Response `200` (`ProcessResponse`):**

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | integer | Created job ID |
| `status` | string | Always `"pending"` |
| `guest_token` | string | Included for guest users |

**Errors:**
- `400` — Invalid extraction method, missing provider/model, missing schema
- `404` — File not found
- `429` — Daily demo limit exceeded

---

### GET `/api/process/status/{job_id}`

Get processing job status.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job ID |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | No | `Bearer <token>` |
| `X-Guest-Token` | string | No | Guest token |

**Response `200` (Job):**

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | integer | Job ID |
| `file_name` | string | Original filename |
| `file_type` | string | File type category |
| `status` | string | One of: `pending`, `processing`, `success`, `error` |
| `provider` | string | Provider used |
| `model` | string | Model used |
| `schema_name` | string | Schema name |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |
| `processing_time` | float | Processing time in seconds |
| `processing_method` | string | Method used |
| `result` | object | Extracted data (when complete) |
| `metadata` | object | Job metadata |
| `error` | string | Error message (if failed) |
| `prompt_tokens` | integer | Token usage |
| `completion_tokens` | integer | Token usage |
| `estimated_cost` | float | Estimated API cost |
| `document_type` | string | Detected document type |
| `correction_status` | string | One of: `uncorrected`, `corrected` |
| `correction_summary` | object | Latest correction summary |
| `hybrid_diagnostics` | object | Hybrid processing diagnostics |
| `quality_score` | float | Image quality score |
| `quality_checks` | object | Quality check details |
| `preprocessing_applied` | string[] | Preprocessing steps applied (e.g. `["deskew", "denoise"]`) |

**Errors:**
- `404` — Job not found

---

## Schemas

### GET `/api/schemas/`

List all schemas.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_template` | boolean | No | Filter by template status |

**Response `200`:** Array of schema objects:

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Schema ID |
| `name` | string | Schema name |
| `description` | string | Schema description |
| `definition` | object | JSON schema definition |
| `is_template` | boolean | Whether it's a template |
| `created_at` | string | ISO 8601 timestamp |
| `updated_at` | string | ISO 8601 timestamp |

---

### POST `/api/schemas/`

Create a new schema.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Schema name (must be unique) |
| `definition` | object | Yes | JSON schema definition |
| `description` | string | No | Schema description |

**Response `200`:** Created schema object (same fields as GET response).

**Errors:**
- `400` — Schema name already exists

---

### GET `/api/schemas/templates`

Get built-in schema templates.

**Response `200`:** Array of template objects:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Template name |
| `definition` | object | JSON schema definition |
| `is_template` | boolean | Always `true` |
| `description` | string | Template description |

---

### POST `/api/schemas/suggestions`

Generate a schema suggestion based on uploaded files using AI.

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | No | `Bearer <token>` |
| `X-Guest-Token` | string | No | Guest token |

**Request Body (`SchemaSuggestRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_ids` | string[] | Yes | List of file IDs to analyze (min 1) |
| `provider` | string | No | Override provider |
| `model` | string | No | Override model |

**Response `200`:** Schema suggestion object.

**Errors:**
- `400` — Failed to generate suggestion
- `404` — File not found

---

### GET `/api/schemas/suggestions/list`

List schema suggestion history. **Requires authentication.**

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Response `200`:** Array of schema suggestion records. Admin users see all; regular users see their own.

---

### GET `/api/schemas/{schema_id}`

Get schema by ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `schema_id` | integer | Yes | Schema ID |

**Response `200`:** Schema object.

**Errors:**
- `404` — Schema not found

---

## Jobs

### GET `/api/jobs/`

List all processing jobs with optional filters. **Requires authentication.**

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `status` | string | No | — | Filter by status |
| `provider` | string | No | — | Filter by provider |
| `limit` | integer | No | `50` | Results per page (1–100) |
| `offset` | integer | No | `0` | Pagination offset |

**Response `200`:** Array of job objects (same shape as process status response). Admin users see all jobs; regular users see their own.

---

### GET `/api/jobs/{job_id}`

Get job by ID. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job ID |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Response `200`:** Job object.

**Errors:**
- `404` — Job not found

---

### DELETE `/api/jobs/{job_id}`

Delete job by ID. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job ID |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Response `200`:**

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | `"Job deleted successfully"` |

**Errors:**
- `404` — Job not found

---

### GET `/api/jobs/{job_id}/corrections`

List all corrections for a job. Supports both authenticated and guest access.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job ID |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | No | `Bearer <token>` |
| `X-Guest-Token` | string | No | Guest token |

**Response `200`:** Array of correction objects.

**Errors:**
- `404` — Job not found

---

### POST `/api/jobs/{job_id}/corrections`

Submit a correction for a completed job. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job ID |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Request Body (`JobCorrectionRequest`):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `corrected_result` | object | Yes | — | The corrected extraction result |
| `feedback_tags` | string[] | No | `[]` | One or more of: `"wrong_field"`, `"missed_field"`, `"bad_type"`, `"layout_issue"` |
| `notes` | string | No | — | Optional reviewer notes |

**Response `200`:** Created correction object.

**Errors:**
- `400` — Job is not successful or has no structured result
- `404` — Job not found

---

## Providers

### GET `/api/providers/`

List all VLM providers and their available models.

**Response `200`:** Array of provider objects:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Provider identifier (e.g., `"openrouter"`, `"gemini"`, `"litellm"`) |
| `display_name` | string | Human-readable name |
| `models` | array | List of available models (strings or objects) |
| `has_api_key` | boolean | Whether an API key is configured |
| `is_default` | boolean | Whether this is the default provider |

---

## Text Processing

### POST `/api/text/process`

Start a text-only extraction job for PDF files. **Requires authentication.**

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Request Body (`TextProcessRequest`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_id` | string | Yes | UUID of uploaded file |
| `provider` | string | Yes | VLM provider name |
| `model` | string | Yes | VLM model name |
| `schema_id` | integer | No | Schema ID |

**Rate limit:** 3 requests/minute

**Response `200`:**

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | integer | Created job ID |

**Errors:**
- `400` — File is not a PDF
- `404` — File not found
- `429` — Daily demo limit exceeded

---

### GET `/api/text/status/{job_id}`

Get text processing job status. **Requires authentication.**

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job ID |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Response `200`:** Job object (same shape as process status response).

**Errors:**
- `404` — Job not found

---

## Quality Check

### POST `/api/quality/check`

Check the quality of an already-uploaded file before processing.

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | No | `Bearer <token>` |

**Request Body (`QualityCheckRequest`):**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file_id` | string | Yes | — | UUID of uploaded file |
| `estimated_dpi` | integer | No | `200` | Estimated DPI for quality assessment |

**Response `200` (`QualityCheckResponse`):**

| Field | Type | Description |
|-------|------|-------------|
| `passed` | boolean | Whether the file passes quality checks |
| `overall_score` | float | Quality score (0–100) |
| `level` | string | Quality level classification |
| `checks` | object | Individual check results |
| `recommendations` | string[] | List of improvement recommendations |
| `auto_fixable_issues` | string[] | Issues that can be auto-fixed |
| `should_reject` | boolean | Whether the file should be rejected |
| `rejection_reason` | string | Reason for rejection (if any) |

**Errors:**
- `400` — File is not an image (JPG/PNG only)
- `404` — File not found
- `500` — Quality check failed

---

### POST `/api/quality/check-upload`

Upload and check image quality in one step. The file is temporarily stored and cleaned up after assessment.

**Request Body:** `multipart/form-data`

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file` | file | Yes | — | Image file (JPG/PNG only) |
| `estimated_dpi` | integer | No | `200` | Estimated DPI for quality assessment |

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | No | `Bearer <token>` |

**Response `200`:** Same as `QualityCheckResponse` above.

**Errors:**
- `400` — Unsupported file type
- `500` — Quality check failed

---

## Benchmarks

### GET `/api/benchmarks/runs`

List benchmark runs with optional filters.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | `50` | Results per page (1–200) |
| `dataset` | string | No | — | Filter by dataset name |
| `provider` | string | No | — | Filter by provider |

**Response `200`:** Array of benchmark run objects.

---

### GET `/api/benchmarks/runs/{run_id}`

Get a benchmark run by ID.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | integer | Yes | Benchmark run ID |

**Response `200`:** Benchmark run object.

**Errors:**
- `404` — Benchmark run not found

---

### GET `/api/benchmarks/runs/{run_id}/results`

Get all results for a benchmark run.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `run_id` | integer | Yes | Benchmark run ID |

**Response `200`:** Array of individual benchmark result objects.

**Errors:**
- `404` — Benchmark run not found

---

### GET `/api/benchmarks/compare`

Get comparison of all models on a dataset.

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `dataset` | string | No | `"cord"` | Dataset to compare |
| `limit` | integer | No | `20` | Max results (1–200) |

**Response `200`:**

| Field | Type | Description |
|-------|------|-------------|
| `runs` | array | Comparison entries sorted by accuracy (descending) |

Each run entry:

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | integer | Run ID |
| `provider` | string | Provider name |
| `model` | string | Model name |
| `processing_method` | string | Method used |
| `sample_count` | integer | Number of samples |
| `overall_accuracy` | float | Accuracy percentage |
| `avg_latency` | float | Average latency in seconds |
| `total_cost` | float | Total cost |
| `total_prompt_tokens` | integer | Total prompt tokens |
| `total_completion_tokens` | integer | Total completion tokens |
| `success_rate` | float | Success rate percentage |
| `started_at` | string | ISO 8601 timestamp |

---

### GET `/api/benchmarks/models`

Return all provider/model combos that have benchmark data.

**Response `200`:** Array of model summary objects:

| Field | Type | Description |
|-------|------|-------------|
| `provider` | string | Provider name |
| `model` | string | Model name |
| `run_id` | integer | Latest run ID |
| `accuracy` | float | Best accuracy |
| `avg_latency` | float | Average latency |
| `total_cost` | float | Total cost |
| `sample_count` | integer | Number of samples |
| `success_rate` | float | Success rate |

---

## Analytics

### GET `/api/analytics/usage`

Get usage analytics for the current user. **Requires authentication.**

**Headers:**

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Authorization` | string | Yes | `Bearer <token>` |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `date_from` | string | No | Start date filter (ISO 8601) |
| `date_to` | string | No | End date filter (ISO 8601) |
| `provider` | string | No | Filter by provider |
| `model` | string | No | Filter by model |
| `schema_name` | string | No | Filter by schema name |
| `processing_method` | string | No | Filter by processing method |
| `document_type` | string | No | Filter by document type |

**Response `200`:** Usage analytics data object.

---

## WebSocket

### WS `/api/ws/job/{job_id}`

WebSocket endpoint for real-time job status updates.

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | integer | Yes | Job ID to subscribe to |

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `token` | string | Yes | JWT authentication token |

**Messages received by client:**

Initial status on connect and subsequent updates:

```json
{
  "type": "status" | "status_update",
  "data": {
    "job_id": 1,
    "file_name": "document.pdf",
    "status": "processing",
    "provider": "openrouter",
    "model": "gpt-4o",
    "result": null,
    "error": null,
    "processing_time": null,
    "processing_method": "vision",
    "created_at": "2026-01-01T00:00:00",
    "completed_at": null,
    "chunking_progress": null
  }
}
```

**Ping/pong:** Client can send `"ping"` text messages; server responds with `"pong"`.

**Close codes:**
- `1008` (Policy Violation) — Invalid token, job not found, or access denied

---

## Health

### GET `/health`

Health check endpoint (no authentication required).

**Response `200`:**

```json
{"status": "healthy"}
```

---

## Common Parameters

### Authentication Header

Most endpoints accept or require a `Authorization: Bearer <token>` header. Tokens are obtained via `POST /api/auth/login`.

### Guest Access

Some endpoints support unauthenticated guest access via `X-Guest-Token` header. Guest tokens are auto-generated on first upload and must be stored by the client for subsequent requests.

### Access Control

- **Admin users** can access all resources regardless of ownership.
- **Authenticated users** can only access their own resources.
- **Guest users** can only access resources created with their guest token.

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP status codes:**

| Code | Description |
|------|-------------|
| `400` | Bad request — invalid parameters or file type |
| `401` | Unauthorized — missing or invalid JWT token |
| `403` | Forbidden — insufficient permissions |
| `404` | Not found — resource does not exist |
| `413` | Payload too large — file exceeds 10 MB |
| `429` | Too many requests — rate limit or daily demo limit exceeded |
| `500` | Internal server error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| General API | 10 requests/minute |
| Upload (`POST /api/upload/`) | 5 requests/minute |
| Processing (`POST /api/process/`, `POST /api/text/process`) | 3 requests/minute |
| Demo users (daily) | 5 requests/day |
