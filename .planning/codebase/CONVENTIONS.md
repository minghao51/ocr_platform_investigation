# Code Conventions

## Overview
This document describes the coding standards, patterns, and conventions used throughout the OCR Platform codebase.

## Python Conventions (Backend)

### Code Style
- **PEP 8 compliant** - Standard Python style guide
- **Type hints** - Used throughout for function signatures
- **Docstrings** - Google-style docstrings for public methods
- **Line length** - Target ~100 chars (soft limit)

### Example:
```python
async def process_file(
    self,
    file_id: str,
    file_path: str,
    file_type: str,
    provider_name: str,
    model: str,
    schema_definition: Dict[str, Any],
    prompt: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Process a file (image or PDF)

    Args:
        file_id: Unique file identifier
        file_path: Path to file on disk
        file_type: Either "image" or "pdf"
        provider_name: VLM provider name
        model: Model identifier
        schema_definition: JSON schema for validation
        prompt: Extraction prompt
        **kwargs: Additional provider-specific args

    Returns:
        Dict with success status and extracted data
    """
```

---

### Async Patterns
**All I/O operations are async**:
- Database: `aiosqlite` with `async with`
- HTTP: `httpx.AsyncClient` with `async/await`
- File I/O: Sync is acceptable (local disk is fast)

**Example**:
```python
async def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM processing_jobs WHERE id = ?",
            (job_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        return None
```

---

### Error Handling
**Pattern**: Try-except with detailed error messages

```python
try:
    result = await provider.process_image(...)
    if "error" in result:
        return {
            "success": False,
            "error": f"Provider error: {result['error']}",
            "raw_response": result
        }
except json.JSONDecodeError as e:
    return {
        "success": False,
        "error": f"Invalid JSON response: {str(e)}",
        "raw_response": result
    }
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

**Logging**: Use `logging` module, not `print()`
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing job {job_id}")
logger.error(f"Failed to process: {error}")
```

---

### Class Structure
**Base classes** for abstractions:
```python
class VLMProvider(ABC):
    """Base class for VLM providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=300.0)

    @abstractmethod
    async def process_image(self, image, prompt, schema, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
```

**Service classes** for business logic:
```python
class ProcessingService:
    """Main processing pipeline"""

    def __init__(self):
        self.providers = {...}
        self.image_service = ImageService()
        self.schema_service = SchemaService()

    def get_provider(self, provider_name: str, api_key: str):
        # Implementation
```

---

### Configuration
**Pydantic Settings** for config:
```python
class Settings(BaseSettings):
    nebius_api_key: str = ""
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    database_url: str = "sqlite:///./data/ocr_platform.db"
    max_file_size: int = 10 * 1024 * 1024

    class Config:
        env_file = "../.env"

@lru_cache
def get_settings():
    return Settings()
```

**Usage**:
```python
settings = get_settings()
api_key = settings.nebius_api_key
```

---

## TypeScript/React Conventions (Frontend)

### Code Style
- **Functional components** - No class components
- **Type strict** - `strict: true` in tsconfig.json
- **No unused locals/params** - Enforced by compiler
- **Arrow functions** - For callbacks and short functions

### Component Pattern
```typescript
interface FileUploadProps {
  onFileSelect: (file: File) => void;
  accept?: string;
  maxSize?: number;
}

function FileUpload({ onFileSelect, accept, maxSize }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    onFileSelect(file);
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
    >
      {/* JSX */}
    </div>
  );
}
```

---

### State Management
**Local state** with hooks:
```typescript
const [jobs, setJobs] = useState<Job[]>([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

**Effects** for side effects:
```typescript
useEffect(() => {
  const interval = setInterval(() => {
    fetchJobStatus(jobId);
  }, 2000);

  return () => clearInterval(interval);
}, [jobId]);
```

**No global state** - No Redux, Zustand, or Context API

---

### API Client Pattern
**Centralized** in `lib/api.ts`:
```typescript
export async function submitJob(params: JobParams): Promise<Job> {
  const formData = new FormData();
  formData.append('file', params.file);
  formData.append('provider', params.provider);
  // ...

  const response = await fetch('/api/processing/upload', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to submit job');
  }

  return response.json();
}
```

**Consistent error handling**:
```typescript
try {
  const result = await submitJob({...});
  setJobId(result.id);
} catch (err) {
  setError(err instanceof Error ? err.message : 'Unknown error');
}
```

---

### TypeScript Types
**Inline interfaces** with components:
```typescript
interface Model {
  id: string;
  name: string;
  provider: string;
}

interface ModelSelectorProps {
  models: Model[];
  selected: string;
  onSelect: (modelId: string) => void;
}
```

**Strict null checks**:
```typescript
// Good
const name: string | null = getName();
if (name) {
  console.log(name.toUpperCase());
}

// Bad (type error)
console.log(name.toUpperCase()); // name might be null
```

---

### Styling Conventions
**TailwindCSS utility classes**:
```tsx
<div className="bg-white rounded-lg shadow-md p-6">
  <h2 className="text-xl font-semibold text-gray-900">
    Title
  </h2>
  <p className="text-gray-600 mt-2">
    Content
  </p>
</div>
```

**Conditional classes**:
```tsx
<button
  className={`
    px-4 py-2 rounded
    ${isActive
      ? 'bg-blue-500 text-white'
      : 'bg-gray-200 text-gray-700'
    }
  `}
>
  Button
</button>
```

**No CSS modules** - All styling via Tailwind

---

### File Naming
- **Components**: `PascalCase.tsx` (e.g., `FileUpload.tsx`)
- **Pages**: `{Name}Page.tsx` (e.g., `HistoryPage.tsx`)
- **Utilities**: `snake_case.ts` (e.g., `api.ts`)
- **Types**: Inline with components (rarely separate files)

---

## Error Handling Conventions

### Backend
**Return structured errors**:
```python
return {
    "success": False,
    "error": "Descriptive message",
    "raw_response": raw_data  # For debugging
}
```

**HTTP exceptions** for API errors:
```python
from fastapi import HTTPException

if not api_key:
    raise HTTPException(
        status_code=400,
        detail=f"No API key configured for {provider_name}"
    )
```

**Log errors** before returning:
```python
import traceback
logger.error(f"ERROR: {error}\n{traceback.format_exc()}")
```

---

### Frontend
**Try-catch** async operations:
```typescript
try {
  await submitJob(params);
} catch (error) {
  setError(error instanceof Error ? error.message : 'Unknown error');
}
```

**User-friendly error messages**:
```typescript
{error && (
  <div className="bg-red-50 text-red-700 p-4 rounded">
    Error: {error}
  </div>
)}
```

**Never expose** raw API errors to users

---

## Database Conventions

### SQL Style
- **Table names**: `snake_case` and plural (e.g., `processing_jobs`)
- **Column names**: `snake_case` (e.g., `file_name`, `created_at`)
- **Primary keys**: `id` (auto-increment)
- **Foreign keys**: `{table}_id` (e.g., `schema_id`)
- **Timestamps**: `created_at`, `completed_at` (ISO 8601 strings)

### Async CRUD Pattern
```python
async def create_job(...) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO processing_jobs (...) VALUES (...)",
            (...)
        )
        await db.commit()
        return cursor.lastrowid

async def get_job(job_id: int) -> Optional[Dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM processing_jobs WHERE id = ?",
            (job_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
```

---

## Testing Conventions

### Test Structure
- **File location**: `backend/tests/`
- **Naming**: `test_{module}.py`
- **Framework**: `pytest` with `pytest-asyncio`

### Test Pattern
```python
import pytest
from services.schema_service import SchemaService

def test_builtin_templates():
    """Test that builtin templates are valid"""
    templates = SchemaService.get_builtin_templates()

    assert "Invoice" in templates
    assert "Receipt" in templates
    assert "ID Card" in templates
    assert "Generic" in templates

@pytest.mark.asyncio
async def test_validate_data():
    """Test data validation"""
    service = SchemaService()
    schema = {"type": "object", "properties": {...}}

    is_valid, data, error = service.validate_data({...}, schema)

    assert is_valid is True
    assert data is not None
```

---

## Comment Conventions

### Python
- **Docstrings** for public methods/classes
- **Inline comments** for complex logic
- **TODOs** are minimal (only one found in codebase)

### TypeScript/React
- **JSDoc** rarely used (types are self-documenting)
- **Comments** for non-obvious JSX logic
- **Descriptive variable names** preferred over comments

---

## Import Conventions

### Python
```python
# Standard library first
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Third-party imports
import httpx
from fastapi import FastAPI
from pydantic import BaseSettings

# Local imports
from services.vlm_provider import VLMProvider
from database import crud
```

### TypeScript
```typescript
// Third-party imports
import { useState, useEffect } from 'react';
import { BrowserRouter } from 'react-router-dom';

// Local imports (absolute path via @ alias)
import { FileUpload } from '@/components/FileUpload';
import { submitJob } from '@/lib/api';
```

---

## Git Conventions

### Commit Messages
**Conventional commits** (observed in history):
```
docs: normalize file naming and remove emojis
docs: reorganize documentation and simplify README
feat: implement text extraction pipeline with pdfplumber
chore: add worktree directories to .gitignore
```

### Branching
- **main** - Production branch
- No formal branching strategy for this small project

---

## Summary of Key Patterns

| Pattern | Backend | Frontend |
|---------|---------|----------|
| Files | `snake_case.py` | `PascalCase.tsx` |
| Classes | `PascalCase` | N/A (functions) |
| Functions | `snake_case` | `camelCase` |
| Constants | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| Async | `async/await` | `async/await` |
| Types | Type hints | TypeScript interfaces |
| Errors | Return dicts + exceptions | Try-catch + state |
| Config | Pydantic Settings | Env variables |
| State | N/A (stateless) | React hooks |
| Styling | N/A | Tailwind classes |
