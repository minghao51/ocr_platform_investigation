# Phase 1: Document Intelligence Features

> Implemented: 2026-04-16

## Overview

Phase 1 extends the OCR Platform beyond PDF/image processing to support comprehensive document intelligence. New extraction methods, file format support, and automatic chunking enable processing of diverse document types at scale.

## New Extraction Methods

### Docling Mode

**Purpose**: Fast, CPU-optimized document processing for digital documents.

**Best For**:
- DOCX, PPTX files with native text content
- PDFs with extractable text layers
- TXT, MD, HTML files
- Documents requiring layout preservation (tables, columns, headers)

**Performance Optimizations**:
- **PyPdfiumDocumentBackend**: 2-3x faster PDF parsing compared to default backend
- **ThreadedPdfPipelineOptions**: Batch processing with configurable batch sizes
  - OCR batch size: 16 pages
  - Layout batch size: 16 pages
  - Table batch size: 2 pages
- **CPU-optimized**: AcceleratorOptions(device=CPU, num_threads=4)
- **Format-specific pipelines**:
  - StandardPdfPipeline for PDF files
  - SimplePipeline for DOCX/PPTX files

**Smart OCR Detection**:
- Automatically detects when OCR is needed
- Skips expensive OCR operations for digital documents
- Falls back to OCR when text layer is missing or poor quality

**API Usage**:
```json
{
  "file_id": "uuid",
  "provider": "nebius",
  "model": "meta-llama/Llama-3.2-90B-Vision-Instruct",
  "extraction_method": "docling",
  "schema_id": 1
}
```

### Transcription Mode

**Purpose**: Faithful Markdown output without JSON schema constraints.

**Best For**:
- Document conversion (PDF → Markdown)
- Content preservation and archiving
- Text extraction when structure is not needed
- Documents requiring human-readable output

**Features**:
- Preserves document structure (headers, lists, tables)
- No JSON schema validation
- Clean, readable Markdown output
- Faster processing than schema-based extraction

**API Usage**:
```json
{
  "file_id": "uuid",
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "extraction_method": "transcription"
}
```

**Note**: Transcription mode does not require `schema_id` or `schema_definition`.

## Automatic Chunking

**Purpose**: Handle documents exceeding model context windows.

**Trigger**: Documents exceeding 80% of model's context window (in tokens).

**Implementation**:
- **MarkdownSplitter**: Header-aware text splitting
- **Token overlap**: 100-token overlap between chunks for context continuity
- **Map-reduce merge**: Individual chunk results merged into coherent output
- **Progress tracking**: WebSocket updates for chunking progress

**Chunking Strategy**:
1. Analyze document token count using tiktoken
2. If exceeds threshold, split on markdown headers
3. Process each chunk independently
4. Merge results preserving document structure

**Supported Models**:
- GPT-4, GPT-3.5 (OpenAI)
- Gemini Flash, Gemini Pro (Google)
- Llama 3.2 Vision (Meta/Nebius)

## Supported File Types

| File Type | Extensions | Extraction Methods | Notes |
|-----------|------------|-------------------|-------|
| PDF | `.pdf` | auto, text, vision, docling, transcription | Auto-routes based on content analysis |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff` | vision, docling | Vision recommended for scans |
| Word | `.docx` | docling, transcription | Native text extraction |
| PowerPoint | `.pptx` | docling, transcription | Native text extraction |
| Text | `.txt`, `.md` | docling, transcription | Direct text processing |
| HTML | `.html` | docling, transcription | HTML to Markdown conversion |

## File Size Limits

- **Maximum file size**: 15 MB
- **Recommended for Docling**: < 10 MB for optimal performance
- **Large files**: Automatically chunked if exceeding context window

## Backend Services

### DoclingService

Location: `backend/services/docling_service.py`

**Features**:
- Format detection (PDF, DOCX, PPTX, images)
- Smart OCR detection
- CPU-optimized pipeline configuration
- Error handling for unsupported formats

**Key Configuration**:
```python
pipeline_options = ThreadedPdfPipelineOptions(
    ocr_batch_size=16,
    layout_batch_size=16,
    table_batch_size=2,
    accelerator_options=AcceleratorOptions(
        device=Device.CPU,
        num_threads=4
    )
)
```

### ChunkingService

Location: `backend/services/chunking_service.py`

**Features**:
- MarkdownSplitter with header-aware splitting
- Token counting using tiktoken
- Configurable overlap and chunk size
- Map-reduce result merging

**Key Configuration**:
```python
splitter = MarkdownSplitter(
    model="gpt-4",  # For token counting
    chunk_size=0.8 * context_window,  # 80% threshold
    overlap=100  # Token overlap
)
```

### TranscriptionService

Location: `backend/services/transcription_service.py`

**Features**:
- Faithful Markdown output
- No schema validation
- Preserves document structure
- Fast processing for digital documents

## Frontend Components

### ExtractionModeSelector

Location: `frontend/src/components/ExtractionModeSelector.tsx`

**Features**:
- Docling mode button
- Transcription mode button
- File type-based mode recommendations
- Visual mode selection

### MarkdownViewer

Location: `frontend/src/components/MarkdownViewer.tsx`

**Features**:
- Markdown content display
- Syntax highlighting
- Copy to clipboard
- Download as .md file

### FileUpload Updates

Location: `frontend/src/components/FileUpload.tsx`

**Features**:
- Accepts DOCX, PPTX, TXT, MD, HTML files
- File type validation
- Size limit enforcement (15MB)
- Format-specific error messages

## Performance Benchmarks

See `docs/benchmarks/phase1.md` for detailed performance comparisons between Docling and traditional PDF parsing methods.

## Migration Notes

### For Existing Users

- **No breaking changes**: Existing extraction methods (auto, text, vision) work as before
- **New defaults**: PDFs now use Docling by default for better performance
- **Schema compatibility**: All existing schemas work with new extraction methods

### For Developers

- **New services**: DoclingService, ChunkingService, TranscriptionService
- **Updated endpoints**: `/api/process/` accepts `docling` and `tr` extraction methods
- **WebSocket events**: New `chunking_progress` event for chunking status

## Known Limitations

1. **DOCX/PPTX tables**: Complex tables may not preserve exact formatting
2. **HTML conversion**: HTML → Markdown conversion may lose some semantic structure
3. **Large file chunking**: Chunking quality depends on document structure (headers help)
4. **Memory usage**: Docling may use more memory for large PDFs with many images

## Future Enhancements

- [ ] Support for Excel files (.xlsx)
- [ ] Advanced chunking strategies (semantic, sentence-based)
- [ ] Table structure preservation for DOCX/PPTX
- [ ] Batch processing for multiple documents
- [ ] Streaming extraction for real-time preview

## Related Documentation

- [API Reference](/docs/reference/api.md)
- [User Guide](/docs/guides/user-guide.md)
- [Project Structure](/docs/reference/project-structure.md)
- [Implementation Plan](/docs/plans/2026-04-16-phase1-document-intelligence-implementation.md)
