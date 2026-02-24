# Backend Architecture

## Entry Point
- `backend/main.py` - FastAPI application, router registration, middleware setup

## Routers (`backend/routers/`)
| File | Purpose |
|------|---------|
| `auth.py` | Login, JWT token management |
| `upload.py` | File upload handling |
| `processing.py` | Document processing orchestration |
| `schemas.py` | Schema CRUD operations |
| `jobs.py` | Job status tracking |
| `providers.py` | VLM provider management |
| `text_processing.py` | Text extraction pipeline |
| `websocket.py` | Real-time updates |

## Services (`backend/services/`)
| File | Purpose |
|------|---------|
| `processing.py` | Main processing pipeline |
| `document_classifier.py` | Auto-routing logic (text vs vision) |
| `text_extraction.py` | PDF text extraction (pdfplumber) |
| `image_service.py` | Image processing |
| `vlm_provider.py` | VLM provider abstraction |
| `nebius.py` | Nebius VLM integration |
| `openrouter.py` | OpenRouter VLM integration |
| `gemini.py` | Google Gemini VLM integration |
| `schema_service.py` | Schema parsing/validation |

## Database (`backend/database/`)
- `crud.py` - Database operations
- `pool.py` - Connection pooling
- `migrations.py` - Schema migrations

## Models (`backend/models/`)
- `schemas.py` - Pydantic request/response models
- `providers.py` - VLM provider models

## Core Files
- `backend/config.py` - Settings management
- `backend/auth.py` - Password hashing, JWT creation
- `backend/dependencies.py` - FastAPI dependencies
- `backend/limiter.py` - Rate limiting
