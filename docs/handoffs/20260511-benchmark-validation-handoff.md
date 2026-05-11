# Prompt Optimization Benchmark Validation Handoff (2026-05-11)

## Context

This session picked up from `20260511-prompt-optimization-handoff.md` and completed the remaining implementation tasks (1, 3, 4, 7), then wired the new features into both benchmark scripts so they exercise the full optimizer pipeline.

---

## What Was Done This Session

### Task 1: Wire quality_score into optimizer [DONE]
- `backend/services/processing.py:190-196` — For image files with vision/hybrid methods, loads image via `ImageService`, runs `QualityGate.assess()`, passes `quality_score` to optimizer
- CoT now triggers when `quality_score < 50` on real image inputs (was dead code before)

### Task 3: Integrate DocumentClassifier for table_heavy/handwritten [DONE]
- `backend/services/processing.py:198-208` — For PDF files, runs `DocumentClassifier().analyze_document()`, auto-selects `table_heavy` (tables + complexity > 70) or `handwritten` (text_density < 50)
- Passes `doc_type` override to optimizer

### Task 4: Add prompt optimization observability [DONE]
- `backend/services/prompt_optimizer.py:70-73` — `logger.info` line: doc_type, cot, hints, quality_score
- `backend/services/processing.py:228-235` — Writes `prompt_optimization` dict to job metadata via `crud.update_job_metadata`

### Task 7: Add ground truth scoring to benchmark_prompts.py [DONE]
- `backend/scripts/benchmark_prompts.py` — Added `--expected` flag (inline JSON or `@file.json`), imports `score_results` from `benchmarks.scoring`, shows accuracy row in output

### Benchmark Enhancement: Wire quality_score + doc_type into both benchmarks [DONE]
- `backend/benchmarks/prompt_optimizer_benchmark.py` — Added `_assess_file()` helper, imports `QualityGate`/`ImageService`/`DocumentClassifier`, passes `quality_score` and `doc_type` to optimizer
- `backend/scripts/benchmark_prompts.py` — Same `_assess_file()` helper and wiring

### Test Results
- 94 unit tests pass, 0 failures, 0 regressions
- Both benchmark scripts import successfully

---

## Benchmark Coverage Verification

### What the benchmarks now exercise

| Feature | `prompt_optimizer_benchmark.py` | `benchmark_prompts.py` |
|---------|------|------|
| Baseline vs optimized A/B | Yes | Yes |
| Doc-type template selection | Yes (from schema_name + classifier) | Yes |
| Schema description enrichment | Yes | Yes |
| XML sandwich formatting | Yes | Yes |
| Learning hints injection | Yes | Yes |
| Chain-of-thought (CoT) | Yes (triggers if quality < 50 or doc_type=handwritten) | Yes |
| Quality gate scoring | Yes (for image files) | Yes (for image files) |
| DocumentClassifier doc_type | Yes (for PDF files) | Yes (for PDF files) |
| Ground truth scoring | Yes (`--expected`) | Yes (`--expected`) |
| CORD dataset mode | Yes (`--dataset cord`) | No (single-file only) |
| Multi-iteration averaging | Yes (`--iterations N`) | No (single run) |

### What is NOT benchmarked
- Raw output / transcription mode (`is_raw_output=True`)
- Layout context injection (`layout_context` parameter)
- Custom prompt override behavior

---

## How to Run the Benchmarks

### Prerequisites
- API keys configured in `.env` (at minimum `GEMINI_API_KEY`)
- `uv sync` from `backend/`

### Single file A/B (simple script)

```bash
cd backend

# Basic run against any document
uv run python scripts/benchmark_prompts.py \
    --file ../data/uploads/sample-invoice.pdf \
    --schema Invoice \
    --provider gemini --model gemini-2.5-flash

# With ground truth for accuracy scoring
uv run python scripts/benchmark_prompts.py \
    --file ../data/uploads/sample-invoice.pdf \
    --schema Invoice \
    --expected '{"invoice_number":"INV-123","total":150.00}'

# Ground truth from file
uv run python scripts/benchmark_prompts.py \
    --file ../data/uploads/sample-invoice.pdf \
    --schema Invoice \
    --expected @/path/to/expected.json
```

### Full benchmark suite (recommended)

```bash
cd backend

# Single file with full report
uv run python -m benchmarks.prompt_optimizer_benchmark \
    --file ../data/uploads/sample-invoice.pdf \
    --schema Invoice \
    --provider gemini --model gemini-2.5-flash \
    --iterations 3

# With ground truth
uv run python -m benchmarks.prompt_optimizer_benchmark \
    --file ../data/uploads/sample-invoice.pdf \
    --schema Invoice \
    --provider gemini --model gemini-2.5-flash \
    --expected '{"invoice_number":"INV-123","total":150.00}'

# CORD receipt dataset (5 samples)
uv run python -m benchmarks.prompt_optimizer_benchmark \
    --provider gemini --model gemini-2.5-flash \
    --dataset cord --max-samples 5
```

### What to look for in results

Key metrics to validate optimizer impact:
1. **Completeness delta** — Optimized should have higher field completeness
2. **Accuracy delta** (with `--expected`) — Ground truth accuracy improvement
3. **CoT enabled** — Should show `True` for blurry images or handwritten docs
4. **Quality score** — Should show numeric value for image inputs
5. **Doc type detected** — Should auto-classify (e.g., `invoice`, `table_heavy`)
6. **Time delta** — Optimized prompts are larger; expect slight increase (acceptable)

---

## Files Changed This Session

| File | Change |
|------|--------|
| `backend/services/processing.py` | Quality gate assessment, DocumentClassifier integration, metadata persistence |
| `backend/services/prompt_optimizer.py` | Added `logger.info` observability line |
| `backend/scripts/benchmark_prompts.py` | `--expected` flag, `_assess_file()`, quality/classifier wiring |
| `backend/benchmarks/prompt_optimizer_benchmark.py` | `_assess_file()`, quality/classifier wiring, enhanced `optimization_meta` |

---

## Remaining / Future Work

| Task | Priority | Notes |
|------|----------|-------|
| Run benchmarks against real documents and record results | HIGH | This is the next step — execute the commands above |
| Add image file benchmark samples to data directory | MEDIUM | Need sample blurry/handwritten images for CoT validation |
| Benchmark raw output / transcription mode | LOW | Not yet covered by either benchmark |
| Extend `_field_hints` dynamically from learning entries | LOW | Static hints don't cover custom schemas |
| Add multi-provider benchmark comparison | LOW | Compare Gemini vs OpenRouter accuracy side-by-side |
