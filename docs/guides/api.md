# API Reference

Complete API documentation for the OCR Platform.

## Interactive Documentation

Once the application is running, access interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Core Endpoints

### Document Processing

#### Upload Document
```
POST /api/upload
```
Upload a document for processing.

**Supported formats**: JPEG, PNG, GIF, WebP, PDF
**Max file size**: 10MB (default)

**Response**: File metadata and temporary storage path

#### Process Document
```
POST /api/process
```
Process an uploaded document with a VLM provider.

**Request body**:
```json
{
  "file_path": "/path/to/uploaded/file",
  "provider": "nebius|openrouter|gemini",
  "model": "model-name",
  "schema": {
    "type": "object",
    "properties": { ... }
  }
}
```

**Response**: Job ID for tracking

#### Get Job Status
```
GET /api/process/status/{job_id}
```
Retrieve the status and results of a processing job.

**Response**:
```json
{
  "job_id": "uuid",
  "status": "pending|processing|completed|failed",
  "result": { ... },
  "error": "error message if failed"
}
```

### Schema Management

#### List Schemas
```
GET /api/schemas
```
Get all custom schemas (built-in templates not included).

#### Create Schema
```
POST /api/schemas
```
Create a custom extraction schema.

**Request body**:
```json
{
  "name": "schema-name",
  "description": "Schema description",
  "schema": {
    "type": "object",
    "properties": { ... }
  }
}
```

#### Get Built-in Templates
```
GET /api/schemas/templates
```
Retrieve all built-in schema templates (Invoice, Receipt, ID Card, Generic).

### Job History

#### List Jobs
```
GET /api/jobs
```
Get all processing jobs with optional filtering.

**Query parameters**:
- `provider`: Filter by provider
- `status`: Filter by status (pending, processing, completed, failed)
- `limit`: Maximum number of jobs to return
- `offset`: Number of jobs to skip

#### Delete Job
```
DELETE /api/jobs/{job_id}
```
Delete a job from history.

### Provider Information

#### List Providers
```
GET /api/providers
```
Get all configured VLM providers and their available models.

**Response**:
```json
{
  "providers": [
    {
      "name": "nebius",
      "models": ["llama-3.2-11b-vision-instruct"]
    },
    {
      "name": "openrouter",
      "models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", ...]
    },
    {
      "name": "gemini",
      "models": ["gemini-1.5-flash", "gemini-1.5-pro"]
    }
  ]
}
```

## Health Check

#### Health Status
```
GET /health
```
Check if the API is running.

**Response**: `{"status": "healthy"}`

## Response Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Internal Server Error |

## Error Handling

All endpoints return consistent error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common errors:
- **Missing API key**: Configure at least one provider in `.env`
- **Invalid file format**: Ensure file is JPEG, PNG, GIF, WebP, or PDF
- **File too large**: Check MAX_UPLOAD_SIZE setting
- **Schema validation failed**: VLM could not extract data matching the schema

## Rate Limits

Rate limiting depends on the configured VLM provider:
- **Nebius**: Based on your Nebius account limits
- **OpenRouter**: Based on your OpenRouter plan
- **Gemini**: Based on Google Cloud quotas

Check your provider dashboards for specific rate limits and quotas.

## Authentication

Currently, the API does not require authentication. In a production environment, you should:
1. Add API key authentication
2. Implement rate limiting per user
3. Add CORS restrictions
4. Use HTTPS only

See [claude.md](../claude.md) for development guidelines on adding security features.
