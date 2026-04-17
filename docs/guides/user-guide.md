# User Guide

## Access Model

- You can browse the landing and methodology pages without logging in.
- You must log in to upload files, run extraction, and view job history.

## Main Screens

### Home

High-level overview of the product and quick links into extraction, history, and methodology.

### Extract

The primary workflow:

1. Upload a PDF or image.
2. Select provider and model.
3. Choose an extraction mode.
4. Select a built-in schema, saved schema, or custom schema.
5. Optionally adjust prompt, temperature, and max tokens.
6. Start processing and watch the live job status.

### History

History shows your prior jobs and lets you:

- filter by status
- filter by provider
- inspect prior results
- delete jobs you no longer want

### Methodology

Explains the difference between auto, text, and vision-oriented processing choices.

## Extraction Modes

### Auto

Recommended default for PDFs. The backend analyzes the document and selects the most suitable pipeline (text or vision).

### Text

Best for digital PDFs with a usable text layer. Faster than vision mode when applicable.

### Vision

Best for images, scans, and visually complex documents. Uses OCR to extract text from visual content.

### Docling-Parse

Unstructured extraction using Docling DocumentConverter:
- **Best for**: Multi-format support (PDF, DOCX, PPTX, images), cost-sensitive processing
- **Performance**: Free extraction, cheap VLM structuring (~$0.01-0.10 per 1000 docs)
- **Features**: Smart OCR detection, layout-aware extraction, table structure preservation
- **Output**: Markdown → VLM structures to JSON
- **Use when**: You need multi-format support or want to minimize API costs

### Docling-Extract

Structured extraction using Docling's local VLM (NuExtract):
- **Best for**: Accuracy-critical applications, privacy-sensitive data, high-volume processing
- **Performance**: Best accuracy (86% vs 69% for cloud VLMs), completely free, 100% private
- **Latency**: Slower (~26s per document)
- **Output**: Direct JSON schema matching (no cloud API needed)
- **Use when**: Accuracy matters most, data privacy is critical, or processing high volumes

### Transcription

Faithful Markdown output without JSON schema constraints:
- **Best for**: Document conversion, content preservation, text extraction
- **Output**: Clean Markdown with headers, lists, and formatting preserved
- **Use when**: You don't need structured JSON, just the document content

### Hybrid

Combined text + vision approach:
- **Best for**: Balancing accuracy and cost
- **Use when**: You want to leverage both extraction methods

### Comparison

| Method | Accuracy | Speed | Cost | Privacy | Best For |
|--------|----------|-------|------|---------|----------|
| **Docling-Extract** | **86%** ⭐ | 26s | **Free** ⭐ | ✅ | Accuracy, privacy |
| **Docling-Parse** | 69%* | 5-10s | $0.01-0.10 | ✅ | Multi-format, cost |
| **Vision** | 69% | 2-4s ⭐ | $0.13-1.21 | ❌ | Speed, non-sensitive |
| **Text** | 65% | 3-5s | $0.01-0.05 | ⚠️ | Pre-extracted text |
| **Hybrid** | 70% | 4-8s | $0.05-0.50 | ⚠️ | Balanced |

*Depends on VLM quality after Docling markdown extraction

## Schemas

You can process documents with:

- built-in templates from the backend
- saved schemas stored in the database
- ad hoc JSON Schema pasted in the editor

Built-in templates currently include:

- `Invoice`
- `Receipt`
- `ID`
- `Generic`

More detail is in [docs/reference/schema-guide.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/schema-guide.md).

## Job Lifecycle

Jobs move through these states:

- `pending`
- `processing`
- `success`
- `error`

Status updates are pushed over WebSocket while the job is running.

## Limits and Constraints

- Login is required for OCR actions.
- Uploads are limited to supported file types: PDF, images, DOCX, PPTX, TXT, MD, HTML.
- Default upload size limit is 15 MB.
- OCR actions are rate-limited per minute for non-admin users.
- Demo accounts can also have a daily OCR cap.
- Admin or master accounts bypass these limits.
- Provider availability depends on which API keys are configured.

### File Type Compatibility

| File Type | Extensions | Extraction Methods |
|-----------|------------|-------------------|
| PDF | `.pdf` | auto, text, vision, docling |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff` | vision, docling |
| Word | `.docx` | docling |
| PowerPoint | `.pptx` | docling |
| Text | `.txt`, `.md` | docling, transcription |
| HTML | `.html` | docling |

## Common Workflow Tips

- Start with `auto` unless you have a specific reason to force another mode.
- Use a small schema first, then expand once extraction quality is stable.
- If one provider/model combination struggles, retry with another before changing your schema.
- Check History instead of rerunning the same document blindly.

## Related Docs

- [docs/guides/setup.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/setup.md)
- [docs/guides/troubleshooting.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/troubleshooting.md)
- [docs/reference/api.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/api.md)
