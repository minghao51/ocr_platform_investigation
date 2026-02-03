# External Integrations

## Overview
The OCR Platform integrates with multiple Vision Language Model (VLM) providers to offer flexible document processing capabilities.

## VLM Providers

### Nebius (meta-llama/Meta-Llama-3.1-70B-Instruct)
**Purpose**: High-performance VLM for document extraction

**Service**: `backend/services/nebius.py`

**Key Features**:
- Base URL: `https://api.studio.nebius.ai/v1`
- Models: Meta-Llama-3.1-70B-Instruct
- Supports both image and text processing
- Default image size: 1024x1024
- Timeout: 300 seconds

**API Key**: `NEBIUS_API_KEY` environment variable

**Usage Flow**:
1. Client uploads document + selects Nebius provider
2. Backend authenticates with API key
3. Document is converted to base64 image (if needed)
4. API call with prompt + JSON schema
5. Response validated against schema
6. Result stored in database

---

### OpenRouter (Multiple Models)
**Purpose**: Multi-model access through unified API

**Service**: `backend/services/openrouter.py`

**Key Features**:
- Base URL: `https://openrouter.ai/api/v1`
- Models: Various (user-selectable)
- Supports both image and text processing
- Default image size: 1024x1024
- Timeout: 300 seconds

**API Key**: `OPENROUTER_API_KEY` environment variable

**Special Behavior**:
- Acts as aggregator for multiple models
- Forwards requests to selected model
- Handles provider-specific quirks

---

### Google Gemini (gemini-2.0-flash-exp)
**Purpose**: Google's VLM with flash processing

**Service**: `backend/services/gemini.py`

**Key Features**:
- Base URL: `https://generativelanguage.googleapis.com/v1beta`
- Models: gemini-2.0-flash-exp
- Supports both image and text processing
- Default image size: 1024x1024
- Timeout: 300 seconds

**API Key**: `GEMINI_API_KEY` environment variable

**Unique Aspects**:
- Uses Google's generation API format
- Specialized in quick "flash" processing
- Different response structure than other providers

---

## Document Processing Libraries

### pdfplumber
**Purpose**: Extract text from digital PDFs

**Service**: `backend/services/text_extraction.py`

**Usage**:
- Used by `TextExtractionService`
- Extracts raw text from PDF text layers
- Falls back gracefully for image-based PDFs
- Fast and cost-effective for digital documents

**Integration Point**:
- Text extraction pipeline
- Called before VLM processing
- Returns empty string for image-only PDFs

---

### PyMuPDF (fitz)
**Purpose**: Fast PDF analysis and classification

**Service**: `backend/services/document_classifier.py`

**Usage**:
- Ultra-fast document triage (<0.1s per document)
- Detects text layers, images, tables
- Calculates complexity scores
- Recommends optimal processing pipeline

**Key Operations**:
- `page.get_text("text")` - Check for text layer
- `page.get_images()` - Detect embedded images
- `page.find_tables()` - Detect table structures
- Page count and layout analysis

---

### pdf2image
**Purpose**: Convert PDF pages to images for VLM processing

**Service**: `backend/services/image_service.py`

**Usage**:
- Converts PDFs to PIL Images
- Handles multi-page documents
- Required for vision-based extraction

---

### Pillow (PIL)
**Purpose**: Image manipulation and encoding

**Service**: `backend/services/image_service.py`, `vlm_provider.py`

**Usage**:
- Resize images to provider requirements
- Convert RGBA to RGB for JPEG encoding
- Base64 encoding for API transmission
- Format: JPEG for compression

---

## Database

### SQLite (via aiosqlite)
**Purpose**: Async embedded database

**Service**: `backend/database/crud.py`

**Schema**:
- `schemas` - JSON schema definitions
- `processing_jobs` - Extraction job records
- `uploaded_files` - File metadata

**Connection**: `sqlite:///./data/ocr_platform.db`

**Async Operations**:
- All database calls use `aiosqlite`
- Context managers for connection cleanup
- Row factory for dict-like results

---

## Frontend Integrations

### Vite Dev Server Proxy
**Config**: `frontend/vite.config.ts`

**Purpose**: Proxy API requests to backend during development

**Proxy Rules**:
```typescript
'/api': {
  target: 'http://localhost:8000',
  changeOrigin: true,
}
```

**Usage**:
- Frontend calls `/api/*` routes
- Vite forwards to `http://localhost:8000/api/*`
- Avoids CORS issues in development

---

### PrismJS
**Purpose**: Syntax highlighting for JSON display

**Component**: `frontend/src/components/ExtractedDataDisplay.tsx`

**Usage**:
- Highlights extracted JSON results
- Provides readable output formatting
- Loaded via `prismjs` npm package

---

## Authentication & Security

### Current State
**No authentication** - Platform is currently single-user with no auth layer

**Security Considerations**:
- CORS is wide-open (`allow_origins=["*"]`)
- API keys stored in environment variables only
- No rate limiting
- No user management

**Future Additions** (if needed):
- API key authentication
- User sessions
- Rate limiting per provider
- CSRF protection

---

## External APIs Not Currently Integrated

### PaddleOCR
**Status**: Temporarily removed due to ARM64 compatibility

**Notes from Code**:
- `backend/services/paddle_ocr_service.py` exists
- Commented out in `pyproject.toml`:
  ```
  # "paddlepaddle>=3.3.0",
  # "paddleocr>=3.3.3",
  ```
- Would enable OCR for scanned documents
- Planned for Phase 2 hybrid pipeline

---

## Error Handling Across Integrations

### Provider Errors
All VLM providers return consistent error format:
```python
{
    "error": "Error message",
    "content": None,
    "model": None,
    "usage": None
}
```

### Timeout Handling
- 300-second timeout for all VLM calls
- Configured in `vlm_provider.py:14`
- Prevents hanging on slow providers

### Retry Logic
**Currently not implemented** - calls fail immediately on error
