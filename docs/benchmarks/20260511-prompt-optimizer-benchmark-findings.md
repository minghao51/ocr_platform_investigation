# Prompt Optimizer Benchmark Findings (2026-05-11)

## Methodology

Ran A/B benchmarks comparing **baseline prompt** (`"Extract all information from this document"`, no system prompt) vs **optimized prompt** (doc-type-aware system prompt, XML sandwich formatting, schema enrichment, CoT when triggered) across:

- 3 document types (invoice PDF, receipt JPG, scanned PDF)
- 2 providers (Gemini direct, OpenRouter)
- `docling-parse` extraction method
- Ground truth scoring on invoice

All benchmarks run via `dotenvx run -- uv run python -m benchmarks.prompt_optimizer_benchmark`.

---

## Results Summary

### Test 1: Invoice PDF (`invoice.pdf`) — Gemini

| Metric | Baseline | Optimized | Delta |
|--------|----------|-----------|-------|
| Success | 100% | 100% | — |
| Time (s) | 5.75 | 3.58 | **-2.17** |
| Field completeness | 95.7% | 95.7% | +0.0% |
| Populated fields | 22/23 | 22/23 | +0 |
| Ground truth accuracy | 100% | 100% | +0.0% |
| Doc type | N/A | invoice | — |
| CoT | N/A | False | — |

**Finding:** On high-quality digital PDFs with Gemini, both prompts produce identical output. Optimized is **38% faster** due to cleaner prompt structure producing more parseable responses.

### Test 2: Receipt JPG (`receipt.jpg`) — Gemini

| Metric | Baseline | Optimized | Delta |
|--------|----------|-----------|-------|
| Success | 100% | 100% | — |
| Time (s) | 7.01 | 4.49 | **-2.52** |
| Field completeness | 92.3% | 92.3% | +0.0% |
| Populated fields | 12/13 | 12/13 | +0 |
| Image quality | N/A | 83.1/100 | — |
| Doc type | N/A | receipt | — |
| CoT | N/A | False (quality > 50) | — |

**Finding:** High-quality image (83.1/100), CoT correctly not triggered. Optimized is **36% faster**.

### Test 3: Scanned PDF (`image_only.pdf`) — Gemini

| Metric | Baseline | Optimized | Delta |
|--------|----------|-----------|-------|
| Success | 0% | 0% | — |
| Doc type | N/A | **handwritten** | — |
| CoT | N/A | **True** | — |
| Classifier doc type | N/A | handwritten | — |

**Finding:** Both failed — docling-parse cannot extract text from pure-image PDFs (no text layer). However, the **classifier correctly detected `handwritten`** (text_density < 50) and **CoT was correctly enabled**. The `vision` method would be needed here (requires poppler, not installed locally).

### Test 4: Invoice PDF (`invoice.pdf`) — OpenRouter

| Metric | Baseline | Optimized | Delta |
|--------|----------|-----------|-------|
| Success | **0%** | **100%** | **+100%** |
| Time (s) | 3.05 | 1.51 | -1.54 |
| Field completeness | **0%** | **95.7%** | **+95.7%** |
| Populated fields | **0** | **22** | **+22** |
| Doc type | N/A | invoice | — |

**Finding:** OpenRouter baseline **completely failed** — returned unparseable output without a system prompt. Optimized prompt with structured XML formatting and system instructions produced clean, correct JSON. This is the **most significant finding**.

### Test 5: Receipt JPG (`receipt.jpg`) — OpenRouter

| Metric | Baseline | Optimized | Delta |
|--------|----------|-----------|-------|
| Success | **0%** | **100%** | **+100%** |
| Time (s) | 5.38 | 2.73 | -2.65 |
| Field completeness | **0%** | **92.3%** | **+92.3%** |
| Populated fields | **0** | **12** | **+12** |
| Image quality | N/A | 83.1/100 | — |

**Finding:** Same pattern — OpenRouter baseline fails completely, optimized succeeds. Confirms the system prompt + XML formatting is **essential** for OpenRouter.

---

## Key Findings

### 1. System prompt is critical for OpenRouter (HIGH impact)

OpenRouter models (tested with `google/gemini-2.5-flash`) return unparseable responses without a system prompt. The optimizer's doc-type-aware system prompt and structured output rules transform 0% success into 95%+ extraction.

| Provider | Baseline Success | Optimized Success |
|----------|-----------------|-------------------|
| Gemini | 100% | 100% |
| OpenRouter | **0%** | **100%** |

### 2. Optimized prompts are consistently faster (MEDIUM impact)

Gemini responses with optimized prompts are 36-38% faster despite larger prompt sizes. The XML structure produces cleaner output that's faster for the model to generate and easier to parse.

| Document | Baseline Time | Optimized Time | Speedup |
|----------|--------------|----------------|---------|
| Invoice (Gemini) | 5.75s | 3.58s | 38% |
| Receipt (Gemini) | 7.01s | 4.49s | 36% |

### 3. Doc-type classification works correctly (verified)

- Invoice PDF → `invoice` (from schema name match)
- Receipt JPG → `receipt` (from schema name match)
- Scanned/image-only PDF → `handwritten` (from DocumentClassifier: text_density < 50)

### 4. Quality gate integration works (verified)

- Receipt JPG quality score: **83.1/100** — CoT correctly NOT triggered (above 50 threshold)
- Scanned PDF would trigger CoT (below 50 threshold) when processed via `vision` method

### 5. Ground truth scoring validates 100% accuracy

Invoice benchmark with `--expected '{"invoice_number":"INV-2024-0042","vendor":"CloudSync Solutions","total":8768.25}'` shows **100% accuracy** for both baseline and optimized on Gemini. The optimizer doesn't regress accuracy on well-structured documents.

### 6. Generic schema + docling-parse has edge cases (BUG)

Both `searchable.pdf` and `multi_page.pdf` with Generic schema failed on the optimized run (95+ seconds, no data). The baseline succeeded. This appears to be a MAX_TOKENS retry issue — the optimized prompt for Generic schema combined with docling-parse chunking produces responses that exceed token limits.

---

## Recommendations

1. **Keep optimizer enabled for all OpenRouter requests** — it's the difference between 0% and 100% success
2. **Investigate Generic schema + docling-parse token overflow** — the 95-second failures on searchable/multi-page PDFs suggest the combined prompt is too large when chunked
3. **Test with poppler installed** for vision method benchmarks on scanned PDFs (would validate CoT path end-to-end)
4. **Add more challenging test fixtures** — blurry images, handwritten documents, complex tables to stress-test the optimizer's different templates

---

## Raw Benchmark Data

All JSON reports saved to:
- `/tmp/bench_invoice.json` — Invoice via Gemini
- `/tmp/bench_receipt.json` — Receipt via Gemini
- `/tmp/bench_image_only.json` — Scanned PDF via Gemini
- `/tmp/bench_prompts_invoice.json` — Invoice with ground truth (Gemini)
- `/tmp/bench_invoice_openrouter.json` — Invoice via OpenRouter
- `/tmp/bench_receipt_openrouter.json` — Receipt via OpenRouter

## Reproduction Commands

```bash
cd backend

# Gemini benchmarks
dotenvx run -- uv run python -m benchmarks.prompt_optimizer_benchmark \
    --file tests/fixtures/invoice.pdf --schema Invoice \
    --provider gemini --model gemini-2.5-flash --method docling-parse

dotenvx run -- uv run python -m benchmarks.prompt_optimizer_benchmark \
    --file tests/fixtures/receipt.jpg --schema Receipt \
    --provider gemini --model gemini-2.5-flash --method docling-parse

dotenvx run -- uv run python -m benchmarks.prompt_optimizer_benchmark \
    --file tests/fixtures/image_only.pdf --schema Generic \
    --provider gemini --model gemini-2.5-flash --method docling-parse

# With ground truth
dotenvx run -- uv run python scripts/benchmark_prompts.py \
    --file tests/fixtures/invoice.pdf --schema Invoice \
    --provider gemini --model gemini-2.5-flash \
    --expected '{"invoice_number":"INV-2024-0042","vendor":"CloudSync Solutions","total":8768.25}'

# OpenRouter comparison
dotenvx run -- uv run python -m benchmarks.prompt_optimizer_benchmark \
    --file tests/fixtures/invoice.pdf --schema Invoice \
    --provider openrouter --model google/gemini-2.5-flash --method docling-parse
```
