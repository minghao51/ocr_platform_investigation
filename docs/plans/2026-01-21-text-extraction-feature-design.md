# Text Extraction Feature Design

**Date:** 2026-01-21
**Status:** Design Approved
**Author:** Collaborative Design with User

## Overview

This document describes the design for a new text extraction feature that adds a parallel processing pipeline to the OCR platform. While the current vision pipeline converts PDFs/images to visual representations for VLM analysis, this new pipeline uses **pdfplumber** for direct text extraction, then passes structured text to text-only LLM models for schema-based extraction.

**Key Benefits:**
- **10-50x faster** than vision model processing
- **5-20x cheaper** by using text-only LLM models
- Ideal for digital/text-based PDFs (invoices, receipts, forms)

## Architecture

### Processing Flow Comparison

```
Vision Pipeline (existing):
Upload → PDF to Images → VLM Vision → JSON extraction

Text Extraction Pipeline (new):
Upload → pdfplumber → Text concatenation → LLM Text → JSON extraction
```

### Key Architectural Changes

1. **New backend endpoint:** `/api/process/text` alongside existing `/api/process`
2. **New service:** `TextExtractionService` using `pdfplumber.extract_text()`
3. **Text processing:** Concatenated with page markers (`--- PAGE N ---`)
4. **Provider system:** Same providers (Nebius, OpenRouter, Gemini) using text-only models
5. **Database schema:** Adds `processing_method` column ("vision" vs "text")
6. **Shared schemas:** Both pipelines use the same JSON schema definitions

### Frontend Navigation

Three tabs:
- **Process** (Vision Extraction) - For images and scanned PDFs
- **Text Extract** (new) - For digital/text-based PDFs
- **History** - View all jobs

## Backend Implementation

### Dependencies

Add to `backend/pyproject.toml`:
```toml
dependencies = [
    ...
    "pdfplumber>=0.11.0",
]
```

Then run: `uv sync`

### New Service: `backend/services/text_extraction.py`

```python
import pdfplumber
from typing import Optional

class TextExtractionService:
    """Extract text from PDFs using pdfplumber"""

    def extract_text_from_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Extract text from all pages of a PDF

        Returns:
            Concatenated text with page markers, or None if no text found
        """
        try:
            text_parts = []

            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()

                    if page_text and page_text.strip():
                        text_parts.append(f"\n\n--- PAGE {i} ---\n\n")
                        text_parts.append(page_text)

            if not text_parts:
                return None

            return "".join(text_parts)

        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
```

### Provider Updates

Update `vlm_provider.py` base class and all provider implementations (Nebius, OpenRouter, Gemini):

```python
async def process_text(
    self,
    text: str,
    prompt: str,
    schema_definition: dict,
    model: str,
    **kwargs
) -> dict:
    """
    Process extracted text with text-only LLM

    Returns:
        Same format as process_image() for consistency
    """
    raise NotImplementedError
```

Each provider implements text-only API calls (no image encoding).

### New Router: `backend/routers/text_processing.py`

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/text", tags=["text-processing"])

class TextProcessRequest(BaseModel):
    file_id: str
    provider: str  # 'nebius', 'openrouter', 'gemini'
    model: str
    schema_id: Optional[str] = None

@router.post("/process")
async def process_text_document(
    request: TextProcessRequest,
    background_tasks: BackgroundTasks
):
    """
    Start text extraction job
    """
    # Create job record with processing_method='text'
    job_id = await crud.create_job(
        file_id=request.file_id,
        provider=request.provider,
        model=request.model,
        schema_id=request.schema_id,
        processing_method='text'  # NEW FIELD
    )

    # Queue background processing
    background_tasks.add_task(
        run_text_processing_job,
        job_id,
        request.file_id
    )

    return {"job_id": job_id}

@router.get("/status/{job_id}")
async def get_text_job_status(job_id: int):
    """Get job status (reuses existing jobs table)"""
    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_404=404, detail="Job not found")
    return job
```

### Database Migration

Add to `backend/database/schema.sql`:

```sql
-- Add processing_method column to jobs table
ALTER TABLE jobs ADD COLUMN processing_method TEXT DEFAULT 'vision';

-- Valid values: 'vision', 'text'
CREATE INDEX idx_jobs_processing_method ON jobs(processing_method);
```

Update migration script in `backend/database/migrations.py` to apply this schema change.

### Background Job Updates

Modify `run_processing_job()` in `services/processing.py`:

```python
async def run_processing_job(job_id: int, file_path: str) -> None:
    """Run processing job (routes based on processing_method)"""
    job = await crud.get_job(job_id)
    if not job:
        return

    processing_method = job.get('processing_method', 'vision')

    if processing_method == 'text':
        await run_text_processing_job(job_id, file_path)
    else:
        # Existing vision processing logic
        await run_vision_processing_job(job_id, file_path)
```

New function in `text_processing.py`:

```python
async def run_text_processing_job(job_id: int, file_path: str) -> None:
    """Run text extraction job"""
    from services.text_extraction import TextExtractionService
    from services.vlm_provider import get_provider

    job = await crud.get_job(job_id)
    await crud.update_job_status(job_id, "processing")

    try:
        # Extract text
        text_service = TextExtractionService()
        extracted_text = text_service.extract_text_from_pdf(file_path)

        if not extracted_text:
            await crud.update_job_status(
                job_id,
                "error",
                error_message="This PDF appears to be image-based. Please use the Vision Extraction tab instead."
            )
            return

        # Get provider and process
        provider = get_provider(job['provider'], job['model'])
        result = await provider.process_text(
            text=extracted_text,
            prompt="Extract all information from this document",
            schema_definition=schema_definition,
            model=job['model']
        )

        # Validate and store result
        ...

    except Exception as e:
        await crud.update_job_status(job_id, "error", error_message=str(e))
```

### Response Schema

Update job response to include text extraction metadata:

```python
{
    "job_id": 123,
    "status": "success",
    "processing_method": "text",
    "result": {...},
    "metadata": {
        "extracted_text_length": 2450,
        "page_count": 3,
        "extracted_text_preview": "Invoice #12345...\n\n--- PAGE 1 ---\n\n..."
    }
}
```

## Frontend Implementation

### Navigation: `frontend/src/App.tsx`

```typescript
type Page = 'processing' | 'text-extraction' | 'history';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('processing');

  return (
    <nav>
      {/* Existing tabs */}
      <button onClick={() => setCurrentPage('processing')}>Vision Extract</button>
      <button onClick={() => setCurrentPage('text-extraction')}>Text Extract</button>
      <button onClick={() => setCurrentPage('history')}>History</button>
    </nav>
    <main>
      {currentPage === 'processing' && <ProcessingPage />}
      {currentPage === 'text-extraction' && <TextExtractionPage />}
      {currentPage === 'history' && <HistoryPage />}
    </main>
  );
}
```

### New Page: `frontend/src/pages/TextExtractionPage.tsx`

Similar structure to `ProcessingPage.tsx` with key differences:

**Features:**
- Uses `/api/text/process` endpoint
- Info banner: "Best for text-based PDFs (digital documents). Use Vision tab for scanned documents."
- Reuses `FileUpload`, `ModelSelector`, `SchemaEditor` components
- After processing: displays expandable "Extracted Text" section above JSON result

**Expandable Text Section:**
```tsx
{jobResult.processing_method === 'text' && (
  <details className="mt-4">
    <summary className="cursor-pointer font-medium">
      Extracted Text ({jobResult.metadata.extracted_text_length} chars,
      {jobResult.metadata.page_count} pages)
    </summary>
    <div className="mt-2 p-4 bg-gray-50 rounded border">
      <pre className="whitespace-pre-wrap text-sm">
        {jobResult.metadata.extracted_text_preview}
      </pre>
    </div>
  </details>
)}
```

### API Client: `frontend/src/lib/api.ts`

```typescript
export async function processTextDocument(
  fileId: string,
  provider: string,
  model: string,
  schemaId?: string
): Promise<{ job_id: number }> {
  const response = await fetch(`${API_BASE}/text/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      file_id: fileId,
      provider,
      model,
      schema_id: schemaId
    })
  });

  if (!response.ok) {
    throw new Error('Failed to process text document');
  }

  return response.json();
}
```

### History Page Updates

Add column for processing method:
```tsx
<table>
  <thead>
    <tr>
      <th>Job ID</th>
      <th>Method</th> {/* NEW */}
      <th>File</th>
      <th>Status</th>
      ...
    </tr>
  </thead>
  <tbody>
    {jobs.map(job => (
      <tr key={job.job_id}>
        <td>{job.job_id}</td>
        <td>
          <span className={
            job.processing_method === 'text' ? 'badge-green' : 'badge-blue'
          }>
            {job.processing_method}
          </span>
        </td>
        ...
      </tr>
    ))}
  </tbody>
</table>
```

## Error Handling

### PDF Has No Text (Scanned Documents)

**Detection:** `pdfplumber.extract_text()` returns empty string or None

**Backend Response:**
```json
{
  "success": false,
  "error": "This PDF appears to be image-based. Please use the Vision Extraction tab instead."
}
```

**Frontend:** Display error with action button:
```
⚠️ No text found in this PDF. It appears to be a scanned document.

[Switch to Vision Extraction]
```

### Corrupted or Invalid PDFs

**Detection:** pdfplumber raises exception during file open

**Backend Response:**
```json
{
  "success": false,
  "error": "Unable to read PDF file. The file may be corrupted."
}
```

### Text Extraction Timeout

**Detection:** Processing exceeds 30 seconds

**Backend Response:**
```json
{
  "success": false,
  "error": "PDF too large for text extraction. Try splitting into smaller files or use Vision Extraction."
}
```

**Implementation:** Add page limit of 50 pages for text extraction

### Memory Management

**Character Limit:** 100,000 characters (~50 pages of text)

**Implementation:**
```python
MAX_TEXT_LENGTH = 100_000

if len(extracted_text) > MAX_TEXT_LENGTH:
    extracted_text = extracted_text[:MAX_TEXT_LENGTH]
    warning = "Text truncated to 100,000 characters. Document may be too large."
```

### Empty LLM Response

**Detection:** LLM returns empty or invalid JSON

**Handling:** Reuse existing schema validation logic from vision pipeline

### Provider Model Validation

**Implementation:** Provider classes validate model names support text processing

**Fallback:** Use default text model if invalid model specified

## Testing Strategy

### Unit Tests: `backend/tests/test_text_extraction.py`

```python
def test_extract_text_from_simple_pdf():
    """Verify pdfplumber extracts text correctly"""
    service = TextExtractionService()
    text = service.extract_text_from_pdf("tests/fixtures/digital.pdf")
    assert text is not None
    assert "--- PAGE 1 ---" in text

def test_extract_text_from_multi_page_pdf():
    """Test page markers are added"""
    text = service.extract_text_from_pdf("tests/fixtures/multi_page.pdf")
    assert "--- PAGE 1 ---" in text
    assert "--- PAGE 2 ---" in text

def test_extract_text_from_image_pdf_returns_empty():
    """Verify scanned PDFs handled"""
    text = service.extract_text_from_pdf("tests/fixtures/scanned.pdf")
    assert text is None

def test_text_too_large_truncates():
    """Test character limit enforcement"""
    # Mock large PDF
    # Verify truncation and warning

def test_provider_process_text_method():
    """Mock LLM API calls"""
    # Test with each provider
```

### Integration Tests

```python
async def test_digital_pdf_text_extraction():
    """Upload digital invoice → process → verify JSON"""
    # Upload file
    # Call /api/text/process
    # Poll status until complete
    # Verify processing_method='text'
    # Verify extracted_text_length > 0
    # Verify result matches schema

async def test_scanned_pdf_error_message():
    """Upload scanned PDF → verify error"""
    # Upload scanned PDF
    # Process with text extraction
    # Verify error message
    # Verify job status='error'

async def test_multi_page_concatenation():
    """Verify page markers in extracted text"""
    # Process 3-page PDF
    # Verify "--- PAGE X ---" markers present

async def test_all_providers_text_models():
    """Test with each provider using text models"""
    for provider in ['nebius', 'openrouter', 'gemini']:
        # Process with text model
        # Verify success
```

### Manual Testing Checklist

- [ ] New "Text Extract" tab appears and is selectable
- [ ] Can upload PDF in Text Extract tab
- [ ] Digital/invoice PDF processes successfully
- [ ] Results show expandable "Extracted Text" section
- [ ] Raw text shows page markers correctly
- [ ] Character count and page count display accurately
- [ ] Scanned/image PDF shows clear error message
- [ ] Error message suggests using Vision tab
- [ ] Processing is noticeably faster than Vision tab
- [ ] Same schemas available in both tabs
- [ ] History page shows processing_method for each job
- [ ] Can filter history by extraction method

### Performance Benchmarks

Compare processing time and cost between Vision and Text extraction:

| Document Type | Vision Pipeline | Text Pipeline | Speedup |
|---------------|-----------------|---------------|---------|
| 1-page invoice | 5-8 seconds | 0.5-1 second | 10-16x |
| 5-page invoice | 20-30 seconds | 1-2 seconds | 15-30x |
| Token cost | Vision API tokens | Text tokens only | 5-20x cheaper |

Track these metrics in production to validate optimization goals.

## Implementation Order

1. **Backend - Core (Day 1)**
   - Add pdfplumber dependency
   - Create TextExtractionService
   - Update provider base class with process_text()
   - Implement text processing in NebiusProvider

2. **Backend - API (Day 1-2)**
   - Create text_processing router
   - Database migration for processing_method
   - Update background job routing
   - Implement error handling

3. **Backend - Complete Providers (Day 2)**
   - Implement process_text() in OpenRouterProvider
   - Implement process_text() in GeminiProvider

4. **Frontend - UI (Day 2-3)**
   - Create TextExtractionPage component
   - Update App.tsx navigation
   - Update API client
   - Update HistoryPage

5. **Testing (Day 3)**
   - Write unit tests
   - Write integration tests
   - Manual testing checklist
   - Performance benchmarks

6. **Documentation (Day 3)**
   - Update README with new feature
   - Update user guide
   - Add examples

## Success Criteria

- [ ] Text extraction is 10-50x faster than vision for text-based PDFs
- [ ] Cost is 5-20x lower than vision pipeline
- [ ] Same schemas work in both Vision and Text tabs
- [ ] Clear error messages for scanned PDFs with helpful guidance
- [ ] Extracted text is visible to users in expandable section
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual testing checklist complete
- [ ] No regressions in existing Vision pipeline

## Notes

- **pdfplumber vs alternatives:** pdfplumber chosen for excellent text extraction quality, simple API, and good PDF layout preservation
- **Separate tabs vs auto-detection:** Separate tabs chosen for clarity and user control, though auto-detection could be added later
- **Text model selection:** Using existing providers in text-only mode keeps infrastructure simple
- **Character limit:** 100k characters chosen as balance between capability and resource usage
- **Page limit:** 50 pages chosen to prevent timeout issues with large documents
