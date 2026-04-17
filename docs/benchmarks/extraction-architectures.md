# Document Extraction Architectures Comparison

> Date: 2026-04-17
> Dataset: CORD (receipt images)
> Benchmarks: 3 approaches compared

## Executive Summary

Three distinct document extraction architectures exist, each with different trade-offs:

| Architecture | Input | Technology | Accuracy | Latency | Cost | Privacy |
|--------------|-------|------------|----------|---------|------|---------|
| **VLM (Cloud)** | Image | Gemini/Qwen vision | 63-69% | 2-4s | $0.13-1.21/1K | ❌ |
| **Docling DocumentExtractor** | Image | NuExtract (local VLM) | **86%** | 26s | **$0** | ✅ |
| **Docling DocumentConverter** | Image/PDF | EasyOCR + layout | N/A | 0.3-5s | **$0** | ✅ |

---

## Architecture 1: Cloud VLMs

### Pipeline

```
Receipt Image
     ↓
   [VLM API]
   ├─ Gemini 3 Flash / Qwen3.5 / etc.
   ├─ Multimodal vision (processes image directly)
   └─ JSON Schema enforcement
     ↓
Structured JSON ({total, items[]})
```

### Code Example

```python
from benchmarks.runner import _process_single_sample

image = Image.open(sample.image_path)  # Direct image input
vlm_result = await provider.process_image(
    image,           # VLM processes image pixels
    prompt="Extract receipt data",
    schema={"total": "float", "items": [...]},
    model="gemini-3-flash-preview"
)
```

### Characteristics

**Pros:**
- ✅ Fast (2-4s per document)
- ✅ No setup/maintenance
- ✅ Auto-scaling
- ✅ Multimodal (understands context, layout)

**Cons:**
- ❌ API costs ($0.13-1.21 per 1000 docs)
- ❌ Privacy (data leaves your infrastructure)
- ❌ Rate limits
- ❌ Network dependency

### Benchmark Results (CORD)

| Model | Accuracy | Median | Items Matched | Latency | Cost/1K |
|-------|----------|--------|---------------|---------|---------|
| Gemini 3 Flash | 68.6% | 74% | 95.7% | 4.0s | $1.21 |
| Gemini 2.5 FL | 66.8% | 74% | 87.8% | 3.2s | $0.13 |
| Qwen3.5 Flash | 63.8% | 72% | 87.1% | 1.9s | $0.13 |

### Best For
- Low-latency requirements (< 5s)
- Burst/sporadic workloads
- Prototyping/MVP
- Non-sensitive data

---

## Architecture 2: Docling DocumentExtractor

### Pipeline

```
Receipt Image
     ↓
[Docling DocumentExtractor]
  ├─ NuExtract model (local VLM)
  ├─ 729 weights (~1GB RAM)
  ├─ Multimodal vision (processes image directly)
  └─ JSON Schema enforcement
     ↓
Structured JSON ({total, items[]})
```

### Code Example

```python
from docling.document_extractor import DocumentExtractor
from docling.datamodel.base_models import InputFormat

extractor = DocumentExtractor(allowed_formats=[InputFormat.IMAGE])
result = extractor.extract(
    source="receipt.png",
    template={"total": "float", "items": [...]}
)
extracted = result.pages[0].extracted_data
```

### Characteristics

**Pros:**
- ✅ **Best accuracy** (86% vs 69%)
- ✅ **Free** (no API costs)
- ✅ **Private** (local processing)
- ✅ **High item matching** (98.6%)
- ✅ No rate limits

**Cons:**
- ❌ Slow (26s per document)
- ❌ High memory (~1GB RAM)
- ❌ Setup required (install dependencies)
- ❌ GPU recommended for speed

### Benchmark Results (CORD, 50 samples)

| Metric | Value |
|--------|-------|
| **Accuracy** | **86.03%** |
| **Median** | **94.74%** |
| **Success (≥50%)** | **96%** |
| **Perfect (≥95%)** | **50%** |
| **Items Matched** | **98.6%** |
| **Latency** | 26s (mean) |
| **Cost** | **$0** |

### Dependencies

```bash
uv add docling
uv add qwen-vl-utils  # Required for NuExtract model
uv add torch  # Backend for NuExtract
```

### Best For
- Accuracy-critical applications
- High-volume processing (amortizes setup cost)
- Privacy-sensitive data (finance, healthcare)
- Cost-sensitive workloads

---

## Architecture 3: Docling DocumentConverter

### Pipeline

```
Receipt Image/PDF
     ↓
[Docling DocumentConverter]
  ├─ EasyOCR (text recognition)
  ├─ Layout analysis (traditional CV)
  ├─ TableFormer (table structure)
  └─ No VLM / no schema enforcement
     ↓
Markdown/text (unstructured)
```

### Code Example

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions

converter = DocumentConverter()
result = converter.convert("receipt.png")
markdown = result.document.export_to_markdown()
```

### Characteristics

**Pros:**
- ✅ **Fast** (0.3-5s per document)
- ✅ **Free** (no API costs)
- ✅ **Private** (local processing)
- ✅ Low memory (~100MB)
- ✅ Multi-format (PDF, DOCX, PPTX, images)
- ✅ No VLM required

**Cons:**
- ❌ **Unstructured output** (markdown/text)
- ❌ Requires post-processing for structured data
- ❌ No direct schema enforcement
- ❌ May miss complex relationships

### Benchmark Results (Simple PDFs)

| Document Type | Time (warm) | Memory | Quality |
|---------------|-------------|--------|---------|
| Small searchable PDF | 155ms | 8MB | 100% |
| Large searchable PDF | 5.4s | 28MB | 100% |
| Image-only PDF (OCR) | 3.0s | 167MB | 95% |

### Dependencies

```bash
uv add docling
uv add easyocr  # For OCR (optional)
```

### Best For
- **Unstructured extraction** (RAG, search, archival)
- High-volume document processing
- Resource-constrained environments
- Multi-format support needed
- **Post-processing with LLM** (hybrid approach)

---

## Hybrid Approach: DocumentConverter + LLM

### Pipeline

```
Receipt Image/PDF
     ↓
[DocumentConverter] → Markdown (fast, cheap)
     ↓
   [LLM API]
   ├─ Text-only (cheaper than vision)
   ├─ Smaller context (markdown vs raw pixels)
   └─ JSON Schema enforcement
     ↓
Structured JSON ({total, items[]})
```

### Why This Works

1. **DocumentConverter** extracts text quickly (0.3-5s)
2. **LLM text API** is cheaper than vision API
3. **Smaller context** (markdown tokens vs image pixels)
4. **Best of both**: speed + cost + structure

### Code Example

```python
# Step 1: Extract text with Docling
converter = DocumentConverter()
result = converter.convert("receipt.png")
markdown = result.document.export_to_markdown()

# Step 2: Structure with text LLM (cheaper than vision)
llm_result = await llm.complete(
    prompt=f"Extract from: {markdown}",
    schema={"total": "float", "items": [...]}
)
```

### Cost Comparison (1000 docs)

| Approach | Extraction | Structuring | Total |
|----------|------------|-------------|-------|
| VLM Vision | - | $130-1210 | $130-1210 |
| DocumentExtractor | $0 | $0 | $0 |
| **Hybrid** | $0 | ~$10-50 | **$10-50** |

### Best For
- Balancing cost and accuracy
- When some structure needed but not critical
- Batch processing (can optimize LLM calls)

---

## Decision Matrix

| Requirement | Best Approach |
|-------------|---------------|
| **Highest accuracy** | Docling DocumentExtractor (86%) |
| **Lowest latency** | VLM Cloud (2-4s) |
| **Lowest cost** | Docling (DocumentExtractor or Converter) |
| **Privacy required** | Docling (any) |
| **Unstructured output** | Docling DocumentConverter |
| **Structured output** | VLM or DocumentExtractor |
| **Multi-format support** | Docling DocumentConverter |
| **No setup/maintenance** | VLM Cloud |
| **High volume** | Docling (amortizes setup) |
| **Burst/sporadic** | VLM Cloud |

---

## Performance Summary

### Accuracy (CORD Receipts)

```
Docling DocumentExtractor:  ████████████████████████ 86%
Gemini 3 Flash:             ████████████████████     69%
Gemini 2.5 Flash Lite:      ███████████████████      67%
Qwen3.5 Flash:              ██████████████████       64%
```

### Latency (per document)

```
Qwen3.5 Flash:              █ 1.9s
Gemini 2.5 FL:              ██ 3.2s
Gemini 3 Flash:             ███ 4.0s
Docling DocumentConverter:  ████ 5s (large PDF)
Docling DocumentExtractor:  ████████████████████████████████ 26s
```

### Cost (per 1000 documents)

```
Docling (both):             $0
Qwen3.5 Flash:              $13
Gemini 2.5 FL:              $13
Gemini 3 Flash:             $121
```

---

## Running Benchmarks

### VLM Cloud Benchmark

```bash
# Uses existing benchmark runner
cd backend
uv run python -m benchmarks.runner \
  --provider openrouter \
  --model gemini-3-flash-preview \
  --dataset cord \
  --samples 50
```

### Docling DocumentExtractor Benchmark

```bash
cd backend
uv run python scripts/benchmark_cord_docling.py
```

### Docling DocumentConverter Benchmark

```bash
cd backend
uv run python scripts/benchmark_docling.py
```

---

## Key Takeaways

1. **Docling DocumentExtractor is NOT traditional CV** - it uses a local VLM (NuExtract)
2. **VLMs process images directly** - not pre-extracted text
3. **DocumentExtractor > VLMs for accuracy** (86% vs 69%) but slower
4. **DocumentConverter for unstructured** - fast, cheap, multi-format
5. **Hybrid approach** balances cost and structure

---

## Related Documentation

- [CORD VLM Benchmark Results](/docs/reference/benchmark-results-cord.md)
- [Phase 1 Docling vs pdfplumber](/docs/benchmarks/phase1.md)
- [Docling Documentation](https://docling-project.github.io/docling/)
