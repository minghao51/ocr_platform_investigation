# API Reference

Base path: `/api`

The API is JWT-protected for file upload, processing, job access, and token verification.

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

Requires authentication. Accepts multipart form data with a `file` field.

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

Requires authentication.

Request fields:

- `file_id`
- `provider`
- `model`
- either `schema_id` or `schema_definition`
- optional `extraction_method`
- optional `prompt`
- optional `temperature`
- optional `max_tokens`

Example:

```json
{
  "file_id": "uuid",
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "schema_id": 1,
  "extraction_method": "auto"
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

### GET/WS `/api/ws/job/{job_id}?token=<jwt>`

Authenticated WebSocket channel for live job status updates.

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
