# API Reference

Base path: `/api`

The API mixes JWT-protected and guest-capable routes. Job listing and admin analytics are JWT-protected; upload and processing support guest access via `X-Guest-Token`.

## Authentication

### POST `/api/auth/login`

Request:

```json
{
  "username": "admin",
  "password": "secret"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "is_admin": true
  }
}
```

### POST `/api/auth/verify`

Requires `Authorization: Bearer <token>`.

Returns the authenticated user payload.

### POST `/api/auth/logout`

Requires `Authorization: Bearer <token>`.

Revokes active JWT sessions for the current user by rotating token version.

## Health

### GET `/health`

Response:

```json
{
  "status": "healthy"
}
```

## Upload

### POST `/api/upload/`

Accepts multipart form data with a `file` field. Works with either:
- `Authorization: Bearer <token>` for authenticated users
- no JWT (guest flow), where `X-Guest-Token` is accepted/returned

Response:

```json
{
  "file_id": "uuid",
  "file_name": "invoice.pdf",
  "file_type": "pdf",
  "file_size": 12345
}
```

## Providers

### GET `/api/providers/`

Lists supported providers and whether they currently have credentials configured.

## Schemas

### GET `/api/schemas/`

Optional query:

- `is_template=true|false`

### POST `/api/schemas/`

Create a saved schema.

Request:

```json
{
  "name": "Invoice Lite",
  "description": "Minimal invoice extraction",
  "definition": {
    "type": "object",
    "properties": {
      "invoice_number": { "type": "string" }
    }
  }
}
```

### GET `/api/schemas/templates`

Returns built-in templates from the backend.

### GET `/api/schemas/{schema_id}`

Returns a single saved schema.

## Processing

### POST `/api/process/`

Works with either authenticated or guest sessions. For guest sessions, include the same `X-Guest-Token` used at upload.

Request fields:

- `file_id`
- `provider`
- `model`
- either `schema_id` or `schema_definition`
- `extraction_method` (required for non-PDF files)
- optional `prompt`
- optional `temperature`
- optional `max_tokens`

**Extraction Methods:**

- `auto` - Recommended for PDFs. Auto-routes based on document analysis
- `text` - For PDFs with extractable text layer
- `vision` - For images, scans, and visually complex documents
- `docling-parse` - Multi-format support (PDF, DOCX, PPTX, images), free extraction + cheap structuring
- `docling-extract` - Local VLM extraction, best accuracy (86%), completely free, private
- `hybrid` - Combined text + vision approach
- `transcription` - Faithful Markdown output without JSON schema constraints

**Extraction Method Comparison:**

| Method | Accuracy | Speed | Cost/1000 docs | Privacy | Best For |
|--------|----------|-------|----------------|---------|----------|
| `docling-extract` | 86% | 26s | $0 | ✅ | Accuracy, privacy |
| `docling-parse` | 69%* | 5-10s | $0.01-0.10 | ✅ | Multi-format |
| `vision` | 69% | 2-4s | $0.13-1.21 | ❌ | Speed |
| `text` | 65% | 3-5s | $0.01-0.05 | ⚠️ | Pre-extracted |
| `hybrid` | 70% | 4-8s | $0.05-0.50 | ⚠️ | Balanced |

*Depends on VLM quality after Docling markdown extraction

Example (PDF with auto routing):

```json
{
  "file_id": "uuid",
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "schema_id": 1,
  "extraction_method": "auto"
}
```

Example (DOCX with Docling-Parse):

```json
{
  "file_id": "uuid",
  "provider": "nebius",
  "model": "meta-llama/Llama-3.2-90B-Vision-Instruct",
  "extraction_method": "docling-parse",
  "schema_definition": {
    "type": "object",
    "properties": {
      "title": { "type": "string" },
      "content": { "type": "string" }
    }
  }
}
```

Example (Receipt with Docling-Extract - local VLM, no API costs):

```json
{
  "file_id": "uuid",
  "extraction_method": "docling-extract",
  "schema_definition": {
    "type": "object",
    "properties": {
      "total": { "type": "number" },
      "items": {
        "type": "array",
        "items": {
          "properties": {
            "name": { "type": "string" },
            "price": { "type": "number" },
            "quantity": { "type": "integer" }
          }
        }
      }
    }
  }
}
```

Example (Transcription mode - no schema):

```json
{
  "file_id": "uuid",
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "extraction_method": "transcription"
}
```

Response:

```json
{
  "job_id": 42,
  "status": "pending"
}
```

### GET `/api/process/status/{job_id}`

Returns the serialized job payload for one processing job.

## Text Route

### POST `/api/text/process`

Dedicated text-processing route. Only valid for PDFs.

### GET `/api/text/status/{job_id}`

Returns text job status using the shared jobs table.

## Jobs

### GET `/api/jobs/`

Requires authentication.

Optional query params:

- `status`
- `provider`
- `limit`

### GET `/api/jobs/{job_id}`

Returns one job if the user has access.

### DELETE `/api/jobs/{job_id}`

Deletes one job if the user has access.

## WebSocket

### POST `/api/ws/ticket`

Requires `Authorization: Bearer <token>`. Returns a short-lived single-use ticket.

### GET/WS `/api/ws/job/{job_id}?ticket=<ticket>`

Authenticated WebSocket channel for live job status updates using the ticket from `POST /api/ws/ticket`.

Message shape:

```json
{
  "type": "status_update",
  "data": {
    "job_id": 42,
    "status": "processing"
  }
}
```

## Source References

- [backend/main.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/main.py)
- [backend/routers/auth.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/auth.py)
- [backend/routers/upload.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/upload.py)
- [backend/routers/processing.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/processing.py)
- [backend/routers/jobs.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/jobs.py)
- [backend/routers/websocket.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/routers/websocket.py)
