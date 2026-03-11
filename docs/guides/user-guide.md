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

Recommended default. For PDFs, the backend analyzes the document and selects the most suitable pipeline.

### Text

Best for digital PDFs with a usable text layer.

### Vision

Best for images, scans, and visually complex documents.

### Hybrid

Accepted by the API, but you should treat `auto`, `text`, and `vision` as the primary supported choices in the current product flow.

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
- Uploads are limited to supported PDF and image types.
- Default upload size limit is 10 MB.
- Provider availability depends on which API keys are configured.

## Common Workflow Tips

- Start with `auto` unless you have a specific reason to force another mode.
- Use a small schema first, then expand once extraction quality is stable.
- If one provider/model combination struggles, retry with another before changing your schema.
- Check History instead of rerunning the same document blindly.

## Related Docs

- [docs/guides/setup.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/setup.md)
- [docs/guides/troubleshooting.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/guides/troubleshooting.md)
- [docs/reference/api.md](/Users/minghao/Desktop/personal/ocr_platform_testdrive/docs/reference/api.md)
