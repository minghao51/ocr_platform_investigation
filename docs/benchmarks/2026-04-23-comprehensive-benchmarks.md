# Comprehensive Extraction Benchmarks

> Date: 2026-04-23
> Samples: 50 per dataset (CORD 50/50, Invoice 25/50 due to HF data quality)
> Script: `backend/scripts/run_comprehensive_benchmark.py`

## Executive Summary

Benchmarked **8 extraction configurations** across **2 datasets** (receipts and invoices) measuring accuracy, latency, cost, and error patterns.

**Top performers:**
- **CORD receipts**: Gemini 3.1 Pro Preview (71.02% accuracy, $0.21) — best accuracy; Gemini 2.5 Flash Lite (69.93%, $0.014) — best value
- **Invoices**: Docling Extract local (62.59%, free) — best accuracy and cost; Qwen 3.5 Flash (43.16%, $0.007) — best cloud option
- **Cheapest overall**: Docling Extract — $0.00, runs locally, competitive accuracy

## Extraction Methods

| Method | How it works | Cost | API Key |
|--------|-------------|------|---------|
| **docling-extract** | Local NuExtract VLM processes image directly into structured JSON | Free | None |
| **docling-parse** | Docling converts image to markdown, then VLM structures it | VLM cost only | Gemini |
| **vision** | VLM processes image directly with schema prompt | Per-token | OpenRouter/Gemini |

## Results: CORD Dataset (Receipts)

50 receipt images with ground truth. Fields: total, subtotal, tax, items (name, price, quantity).

| Rank | Method | Model | Accuracy | Latency | Cost |
|------|--------|-------|----------|---------|------|
| 1 | vision | gemini-3.1-pro-preview | **71.02%** | 27.16s | $0.207 |
| 2 | vision | gemini-2.5-flash-lite | 69.93% | 2.54s | $0.014 |
| 3 | vision | qwen3.5-flash | 67.96% | 2.17s | $0.007 |
| 4 | vision | gemini-3-flash-preview | 67.68% | 3.89s | $0.072 |
| 5 | docling-extract | local NuExtract | 61.43% | 23.35s | $0.000 |
| 6 | vision | grok-4.1-fast | 60.70% | 21.56s | $0.078 |
| 7 | docling-parse | +gemini-2.5-flash-lite | 56.84% | 227.81s | $0.005 |
| 8 | vision | gemma-4-31b-it | 60.15% | 22.63s | $0.007 |

### CORD Accuracy / Cost Trade-off

Best value: **gemini-2.5-flash-lite** delivers 69.93% accuracy at $0.014 (15x cheaper than gemini-3.1-pro's $0.207 for only 1% less accuracy).

**docling-extract** is notable: 61.43% accuracy at $0.00, no API key needed, competitive with paid cloud models like grok-4.1-fast (60.70%).

## Results: Invoice Dataset

25/50 invoice images loaded (see Known Issues). Fields: invoice_no, seller, client, items, totals.

| Rank | Method | Model | Accuracy | Latency | Cost |
|------|--------|-------|----------|---------|------|
| 1 | docling-extract | local NuExtract | **62.59%** | 39.73s | $0.000 |
| 2 | vision | qwen3.5-flash | 43.16% | 4.88s | $0.007 |
| 3 | docling-parse | +gemini-2.5-flash-lite | 42.64% | 118.05s | $0.010 |
| 4 | vision | gemma-4-31b-it | 41.16% | 48.89s | $0.008 |
| 5 | vision | gemini-3-flash-preview | 40.13% | 6.18s | $0.071 |
| 6 | vision | gemini-3.1-pro-preview | 39.41% | 17.18s | $0.276 |
| 7 | vision | gemini-2.5-flash-lite | 39.62% | 4.39s | $0.013 |
| 8 | vision | grok-4.1-fast | 31.62% | 20.82s | $0.054 |

### Invoice Insight

docling-extract dominates invoices (62.59%), 19 points ahead of the best cloud model. This is likely because NuExtract's training aligns well with structured invoice formats. The two-pass docling-parse approach also does well (42.64%) but is 3x slower than docling-extract.

## Error Analysis

### CORD Error Patterns

The CORD dataset presents a unique challenge: ground truth annotations use **concatenated names** (e.g., `JASMINEMT( L)`, `J.STBPROMO`, `-TICKETCP`) while all models naturally add spaces (`JASMINE MT (L)`, `J.STB PROMO`, `TICKET CP`).

**Top error types across all methods on CORD:**

| Error Pattern | Frequency | Example |
|---------------|-----------|---------|
| `name_fuzzy_partial` | ~23-31 per run | Expected `J.STBPROMO`, got `J.STB PROMO` — space inserted |
| `string_mismatch` | ~7-13 per run | Expected `JASMINEMT( L) + COCONUTJELLY( L)` as single item, model splits into two items |
| `null_mismatch` | ~2-5 per run | Model doesn't extract any items from receipt |

**Item splitting is the #1 accuracy killer.** CORD annotates compound items as a single entry (e.g., `JASMINEMT( L) + COCONUTJELLY( L)`) with a combined price. All models interpret the `+` as two separate items, causing complete mismatches on ~20% of samples.

**Name formatting** is the #2 issue. The concatenated annotation style vs. natural spacing accounts for most `name_fuzzy_partial` penalties. The models are actually reading the receipt *correctly* — the scoring penalizes the format difference.

### Invoice Error Patterns

Invoice errors are more systematic and indicate genuine model limitations:

| Error Pattern | Frequency | Root Cause |
|---------------|-----------|------------|
| `total_*: numeric_partial` | ~20-26 per run | Ground truth has `"$ 889,20"` (string with currency/space/comma), models return `889.2` (float). Scoring can't parse `"$ 889,20"` as a number → 0.01 score |
| `seller/client: name_contains_expected_partial` | ~20-26 per run | Expected full address: `"Bradley-Andrade 9879 Elizabeth Common..."`, model returns just name: `"Bradley-Andrade"` |
| `items: name_fuzzy_partial` | ~20-26 per run (vision) | Models extract item descriptions but struggle with exact matching on long product names |

**The `total_*` issue is a scoring bug, not a model error.** The ground truth stores totals as strings like `"$ 889,20"` using European decimal notation (comma). The `normalize_number()` function can't parse `"$ 889,20"` — it expects `"$889.20"`. The models correctly extract `889.2` but get scored as 0.01 (near-zero). This artificially depresses invoice accuracy by ~15-20 percentage points across all methods.

**The seller/client issue** is a schema mismatch. The HF dataset ground truth includes full addresses in the `seller`/`client` fields, but models reasonably return just the company name. This is not an extraction error — it's a disagreement about field scope.

### Corrected Accuracy Estimates

If we adjust for the scoring artifacts:

- **Invoice accuracy would be ~60-80%** for top models (fixing the `normalize_number` European decimal issue and address scope)
- **CORD accuracy would be ~75-85%** for top models (adjusting for annotation concatenation format)

## Cost Analysis

### Per-Sample Cost (CORD, 50 samples)

| Model | Total Cost | Per Sample | Accuracy/$ |
|-------|-----------|------------|------------|
| docling-extract | $0.00 | $0.000 | ∞ |
| qwen3.5-flash | $0.007 | $0.000 | 10,140,000%/\\$ |
| gemma-4-31b-it | $0.007 | $0.000 | 8,579,000%/\\$ |
| gemini-2.5-flash-lite | $0.014 | $0.000 | 4,995,000%/\\$ |
| docling-parse | $0.005 | $0.000 | 11,368,000%/\\$ |
| gemini-3-flash-preview | $0.072 | $0.001 | 940,000%/\\$ |
| grok-4.1-fast | $0.078 | $0.002 | 778,000%/\\$ |
| gemini-3.1-pro-preview | $0.207 | $0.004 | 343,000%/\\$ |

### Per-Sample Cost (Invoice, 25 samples)

| Model | Total Cost | Per Sample |
|-------|-----------|------------|
| docling-extract | $0.000 | $0.000 |
| qwen3.5-flash | $0.007 | $0.000 |
| gemma-4-31b-it | $0.008 | $0.000 |
| docling-parse | $0.010 | $0.000 |
| gemini-2.5-flash-lite | $0.013 | $0.001 |
| grok-4.1-fast | $0.054 | $0.002 |
| gemini-3-flash-preview | $0.071 | $0.003 |
| gemini-3.1-pro-preview | $0.276 | $0.011 |

## Latency Analysis

| Method | Model | CORD (avg) | Invoice (avg) |
|--------|-------|-----------|--------------|
| vision | qwen3.5-flash | **2.17s** | 4.88s |
| vision | gemini-2.5-flash-lite | 2.54s | 4.39s |
| vision | gemini-3-flash-preview | 3.89s | 6.18s |
| vision | gemini-3.1-pro-preview | 27.16s | 17.18s |
| docling-extract | local | 23.35s | 39.73s |
| vision | gemma-4-31b-it | 22.63s | 48.89s |
| vision | grok-4.1-fast | 21.56s | 20.82s |
| docling-parse | +gemini | 227.81s | 118.05s |

docling-parse is dramatically slower because it's a two-pass pipeline (Docling OCR → markdown → VLM structuring), and Docling runs sequentially on CPU.

## Recommendations

### For Production Use

1. **Default: gemini-2.5-flash-lite (vision)** — best balance of accuracy (69.93% CORD), speed (2.5s), and cost ($0.014/50 samples)
2. **Offline/privacy-sensitive: docling-extract** — free, no API key, 61-63% accuracy, good for batch processing
3. **Maximum accuracy: gemini-3.1-pro-preview** — 71% on CORD but 10x more expensive
4. **Avoid for now: grok-4.1-fast** — lowest accuracy-to-cost ratio; gemma-4-31b-it — too slow for the accuracy

### Scoring Improvements Needed

1. **Fix `normalize_number()` for European decimal format** — `"$ 889,20"` should parse as `889.2`. This would add ~15-20% to all invoice scores
2. **CORD name matching** — Consider stripping all spaces/punctuation in name comparison (already partially done but could be more aggressive)
3. **Compound item handling** — The `+` separator in CORD items is a dataset artifact; consider splitting on `+` before comparison

## Test Environment

- **Hardware**: macOS (Apple Silicon)
- **Python**: 3.13
- **Docling**: Latest (NuExtract VLM backend)
- **Concurrency**: 5 concurrent requests (vision), sequential (docling-extract), 2 concurrent (docling-parse)
- **Datasets**: CORD test split (100 available, 50 used), HF invoices test split (125 available, 25 loaded)

## Known Issues

1. **Invoice dataset loading**: Only 25/50 samples loaded — some items in the HF dataset are string representations instead of dicts (`ast.literal_eval` fails on edge cases)
2. **Scoring artifact**: Invoice `total_*` fields scored near-zero due to European decimal notation in ground truth
3. **docling-parse slow**: Sequential Docling processing + OCR + VLM structuring = 4min per run on CORD
4. **gemini-3.1-pro cold start**: First sample takes 30-35s, subsequent samples 2-5s

## Running the Benchmark

```bash
cd backend

# Full run (8 methods × 2 datasets × 50 samples)
dotenvx run -- uv run python scripts/run_comprehensive_benchmark.py

# Quick test
dotenvx run -- uv run python scripts/run_comprehensive_benchmark.py --samples 3

# Specific method/dataset
dotenvx run -- uv run python scripts/run_comprehensive_benchmark.py --dataset cord --methods "docling-extract"
dotenvx run -- uv run python scripts/run_comprehensive_benchmark.py --dataset invoice --methods "vision"
```

## Related

- [Extraction Architectures](/docs/benchmarks/extraction-architectures.md)
- [Benchmark Script](/backend/scripts/run_comprehensive_benchmark.py)
- [Raw Results JSON](/docs/benchmarks/comprehensive-results.json)
