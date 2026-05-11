# VLM Prompt Optimization Handoff (2026-05-11)

## Context

Implemented a `PromptOptimizer` service that enriches VLM extraction prompts using:
- Document-type-aware system prompts (invoice, receipt, ID, table_heavy, handwritten, generic)
- Schema description enrichment from a curated field hint dictionary
- XML sandwich prompt formatting (instructions, schema, hints in structured XML tags)
- Chain-of-thought for low-quality/handwritten documents
- Feedback loop from `prompt_learning_entries` (corrections injected as extraction hints)
- Raw output Markdown fidelity templates

### Files Created
- `backend/services/prompt_templates.py` — Doc-type templates, raw output rules, CoT instructions
- `backend/services/prompt_optimizer.py` — Core `PromptOptimizer` class
- `backend/scripts/benchmark_prompts.py` — A/B prompt comparison CLI
- `backend/benchmarks/prompt_optimizer_benchmark.py` — Full A/B benchmark with ground truth scoring + CORD dataset support
- `backend/tests/unit/test_prompt_optimizer.py` — 39 unit tests for optimizer (all passing)

### Files Modified
- `backend/services/schema_service.py` — Added `description` to all built-in template properties
- `backend/services/gemini.py` — `systemInstruction` support for vision + text, fixed MAX_TOKENS retry
- `backend/services/openrouter.py` — System message for vision extraction
- `backend/services/litellm_provider.py` — System message for vision extraction
- `backend/services/processing.py` — `PromptOptimizer` wired into both `run_processing_job` and `run_text_processing_job`
- `backend/services/processors/vision.py` — Passes `system_prompt` through to provider
- `backend/services/processors/text.py` — Passes `system_prompt` through to provider
- `backend/services/processors/docling_parse.py` — Improved chunk prompts, fixed system_prompt consumed on first chunk
- `backend/services/hybrid_processing.py` — XML-tagged prompt formatting

### Bugs Fixed During Audit
1. **Gemini MAX_TOKENS retry lost `systemInstruction`** — retry payload now preserves it
2. **Docling chunked processing lost `system_prompt` after first chunk** — pre-pop from kwargs, fresh copy per chunk
3. **Auto-generated schema descriptions were misleading** — removed type-based fallbacks, only confident matches
4. **`classify_doc_type_hint` "id" substring matching** — `"id"` key in `_exact_name_map` matched any string containing "id" (e.g., "ValidDocument" if case-lowered with "id" adjacent). Fixed by removing `"id"` from map keys and using word-boundary matching for standalone "id"

### Test Results
- 94 unit tests pass (39 new for prompt optimizer), 0 regressions
- Pre-existing integration failures (schema nesting depth validation) unrelated to changes

---

## Remaining Gaps — Actionable Pickup Tasks

Tasks are ordered by priority. Each has a clear scope, files to change, and acceptance criteria.

---

### Task 1: Wire quality score into optimizer [HIGH]

**Problem:** `quality_score` parameter in `PromptOptimizer.optimize_prompt()` is always `None` because the quality gate runs inside the processor *after* the prompt is built. The CoT trigger for low-quality images (`score < 50`) is dead code in the main flow.

**Scope:**
- Files: `backend/services/processing.py`, `backend/services/processors/vision.py`
- ~50 lines of changes

**Approach:**
1. For `run_processing_job` with vision/hybrid methods: load the image, run `QualityGate.assess()` before calling the optimizer, pass the score
2. For docling-parse/text methods: skip (no image quality applicable)
3. Add `from services.quality_gate import QualityGate` and `from services.image_service import ImageService` to `processing.py`

**Changes in `processing.py` `run_processing_job`** (after line 201):
```python
quality_score = None
if file_type == "image" and extraction_method in ("vision", "hybrid"):
    try:
        img = ImageService().load_image(file_path)
        quality_score = QualityGate().assess(img).overall_score
    except Exception:
        pass
```
Then pass `quality_score=quality_score` to `optimizer.optimize_prompt(...)`.

**Acceptance:**
- `uv run pytest tests/unit/ -x -q` passes
- CoT is triggered when quality score < 50 on image inputs

---

### Task 2: DONE — Unit tests for PromptOptimizer [HIGH]

**Status:** Complete. 39 tests in `backend/tests/unit/test_prompt_optimizer.py`, all passing.

---

### Task 3: Integrate DocumentClassifier for `table_heavy`/`handwritten` auto-selection [MEDIUM]

**Problem:** `classify_doc_type_hint` can only return `invoice`, `receipt`, `id`, or `generic`. The `table_heavy` and `handwritten` templates exist but are never auto-selected.

**Scope:**
- Files: `backend/services/prompt_templates.py`, `backend/services/processing.py`
- Add ~20 lines, modify ~5 lines

**Approach:**
1. In `processing.py` `run_processing_job`, when file is PDF, run `DocumentClassifier().analyze_document(file_path)` (fast, <0.1s via PyMuPDF)
2. Map classifier output to `doc_type`:
   - `has_tables and complexity_score > 70` → `"table_heavy"`
   - `text_density < 50` (scanned) → could be handwritten, but need additional heuristic
3. Pass `doc_type=result_doc_type` to `optimizer.optimize_prompt(...)`
4. Update `classify_doc_type_hint` to also accept classifier data

**Acceptance:**
- PDFs with tables get `table_heavy` doc type automatically
- `uv run pytest tests/unit/ -x -q` passes

---

### Task 4: Add prompt optimization observability [MEDIUM]

**Problem:** No way to know from job results whether the optimizer was used, what doc type was detected, whether CoT was enabled, or if learning hints were injected.

**Scope:**
- Files: `backend/services/prompt_optimizer.py`, `backend/services/processing.py`
- Add ~10 lines

**Approach:**
1. In `prompt_optimizer.py` `optimize_prompt()`, add:
   ```python
   logger.info(
       "Prompt optimized: doc_type=%s, cot=%s, hints=%s",
       resolved_doc_type, use_cot, bool(learning_hints),
   )
   ```
2. In `processing.py` `run_processing_job`, after optimizer call, store metadata:
   ```python
   if result.get("metadata"):
       result["metadata"]["prompt_optimization"] = {
           "doc_type": prompt_result.doc_type_used,
           "cot_enabled": prompt_result.cot_enabled,
           "hints_injected": prompt_result.hints_injected,
       }
   ```
   Or use `crud.update_job_metadata` if metadata is separate.

**Acceptance:**
- Job metadata contains `prompt_optimization` dict
- Log line appears at INFO level during processing

---

### Task 5: NO FIX NEEDED — User `prompt_override` behavior [DOCUMENTED]

When a user provides a custom prompt, the optimizer wraps it in `<instructions>` tags and still applies doc-type detection, schema enrichment, and learning hints. This is correct and useful. The user's text becomes the instruction content.

---

### Task 6: Extend `_field_hints` dynamically [LOW — FUTURE]

**Problem:** Static hint dictionary doesn't cover custom schemas.

**Future approach:**
- Schema authors can already include `description` fields (supported)
- Could mine `prompt_learning_entries` for common field names and correction patterns
- Could add an LLM-based "description suggester" endpoint

---

### Task 7: Add ground truth scoring to `benchmark_prompts.py` [LOW]

**Problem:** The simpler `benchmark_prompts.py` script measures completeness and timing but lacks ground truth comparison.

**Note:** The newer `benchmarks/prompt_optimizer_benchmark.py` already supports `--expected` and uses `scoring.py`. This task is only for the original script if needed.

**Approach:**
- Add `--expected` flag to `backend/scripts/benchmark_prompts.py`
- Import `benchmarks.scoring.score_results`
- Add accuracy column to the comparison table

---

## Key Files for Next Session

| File | Purpose |
|------|---------|
| `backend/services/prompt_optimizer.py` | Core optimizer — start here for any changes |
| `backend/services/prompt_templates.py` | Templates and classification logic |
| `backend/services/processing.py:183-201, 317-331` | Where optimizer is called (Task 1, 3, 4 touch this) |
| `backend/services/document_classifier.py` | Classifier to integrate for Task 3 |
| `backend/services/gemini.py:25, 175` | `system_prompt` pop points |
| `backend/services/quality_gate.py` | Quality gate for Task 1 |
| `backend/benchmarks/prompt_optimizer_benchmark.py` | Benchmark script with ground truth scoring |
| `backend/tests/unit/test_prompt_optimizer.py` | 39 unit tests — add new tests here |

## Validation Commands
```bash
cd backend
uv run pytest tests/unit/ -x -q                                    # All unit tests (94)
uv run pytest tests/unit/test_prompt_optimizer.py -v              # Optimizer tests (39)
uv run python -m benchmarks.prompt_optimizer_benchmark --help     # Benchmark CLI
uv run python -m benchmarks.prompt_optimizer_benchmark \
    --file <path> --schema Invoice \
    --expected '{"invoice_number":"INV-123","total":150.00}'       # Single file A/B
uv run python -m benchmarks.prompt_optimizer_benchmark \
    --dataset cord --max-samples 5                                 # Dataset benchmark
```
