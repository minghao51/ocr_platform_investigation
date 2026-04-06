# CORD Receipt Benchmark Results

> Date: 2026-04-05
> Dataset: CORD (Consolidated Receipt Dataset) via Hugging Face (`katanaml/cord`)
> Samples: 50 from train split (receipt_00000 – receipt_00049)
> Schema: `{total, items[].{name, price, quantity}}` (required: total, items)
> Structured Output: JSON Schema enforcement on all providers
> Scoring v2: Normalized string comparison (space-insensitive) + weighted item matching (name 60%, other fields 40%)

---

## Summary

| Rank | Model | Provider | Accuracy | Median | Items Matched | Items Extracted | Avg Latency | Cost/1000 docs |
|------|-------|----------|----------|--------|---------------|-----------------|-------------|----------------|
| 1 | Gemini 3 Flash Preview | OpenRouter | **68.6%** | 0.75 | 133/139 (95.7%) | 139/139 (100%) | 4.0s | $1.21 |
| 2 | Gemini 2.5 Flash Lite | Direct API | **66.8%** | 0.74 | 122/139 (87.8%) | 140/139 (101%) | 3.2s | $0.13 |
| 3 | Qwen3.5 Flash | OpenRouter | **63.8%** | 0.72 | 121/139 (87.1%) | 139/139 (100%) | 1.9s | $0.13 |

### Key Metrics

| Model | Zero-accuracy | Near-perfect (≥95%) | Success Rate (≥50%) | Min | Max |
|-------|--------------|---------------------|---------------------|-----|-----|
| Gemini 3 Flash | 0 | 0 | 92% | 0.20 | 0.89 |
| Gemini 2.5 FL | 1 | 3 | 86% | 0.00 | 1.00 |
| Qwen3.5 Flash | 1 | 0 | 82% | 0.00 | 0.89 |

---

## Distribution Analysis

### Accuracy Distribution (50 samples)

| Accuracy Range | Gemini 3 Flash | Gemini 2.5 FL | Qwen3.5 Flash |
|---------------|---------------|---------------|---------------|
| 0.00–0.25 | 3 samples | 4 samples | 5 samples |
| 0.26–0.50 | 1 sample | 3 samples | 4 samples |
| 0.51–0.75 | 35 samples | 29 samples | 30 samples |
| 0.76–0.90 | 11 samples | 11 samples | 11 samples |
| 0.91–1.00 | 0 samples | 3 samples | 0 samples |

**Observation**: All models cluster in the 50-75% range for most samples. The spread is narrow — no model dominates consistently.

### Item Extraction Quality

| Metric | Gemini 3 Flash | Gemini 2.5 FL | Qwen3.5 Flash |
|--------|---------------|---------------|---------------|
| Items matched | 95.7% | 87.8% | 87.1% |
| Items extracted | 100.0% | 100.7% | 100.0% |
| Over-extraction | 0 | 1 extra item | 0 |

Gemini 3 Flash has the best item matching (95.7%) — it extracts item names more accurately, including modifiers.

---

## Consistently Difficult Samples

These samples scored below 50% accuracy across multiple models:

| Sample | Gemini 3 | Gemini 2.5 FL | Qwen3.5 | Root Cause |
|--------|----------|---------------|---------|------------|
| 9 | 0.25 | 0.25 | 0.25 | Complex receipt with modifiers |
| 11 | 0.68 | 0.00 | 0.00 | Ground truth has `VietMilkCoffee + +Hot + +M`, VLMs extract `Viet Milk Coffee` |
| 20 | 0.71 | 0.45 | 0.43 | Multiple items with modifiers |
| 24 | 0.77 | 0.20 | 0.20 | Prices hard to read, VLMs skip them |
| 27 | 0.25 | 0.24 | 0.25 | Only items in ground truth, no total |
| 31 | 0.49 | 0.49 | 0.50 | Similar pattern — items only in GT |
| 46 | 0.20 | 0.18 | 0.20 | Prices missing from VLM output |

### Common Failure Patterns

1. **Item modifiers in ground truth**: CORD annotations include modifiers as part of the item name (e.g., `VietMilkCoffee + +Hot + +M`). VLMs extract the base name only (`Viet Milk Coffee`). After normalization (`vietmilkcoffeehotm` vs `vietmilkcoffee`), the Levenshtein ratio is too low.

2. **Samples with items-only ground truth**: Some CORD receipts only have `items` in ground truth, no `total`. The VLM correctly extracts both, but the scoring only compares expected fields. When items don't match well, there's no `total` field to compensate.

3. **Missing prices on certain receipts**: Samples 24, 46 have prices in formats the VLMs struggle with (small font, unusual layout, or currency symbols).

---

## Cost Analysis

| Model | Cost per doc | Cost per 100 docs | Cost per 1000 docs | Cost per 10K docs |
|-------|-------------|-------------------|--------------------|-------------------|
| Qwen3.5 Flash | $0.0001 | $0.01 | $0.13 | $1.34 |
| Gemini 2.5 FL | $0.0001 | $0.01 | $0.13 | $0.13 |
| Gemini 3 Flash | $0.0012 | $0.12 | $1.21 | $12.10 |

**Value ranking (accuracy-points per dollar):**
1. Gemini 2.5 Flash Lite: 514,000 points/$
2. Qwen3.5 Flash: 491,000 points/$
3. Gemini 3 Flash Preview: 56,700 points/$

---

## Recommendations

### For Production Use
- **Best value**: **Gemini 2.5 Flash Lite** — 67% accuracy at $0.13/1000 docs, good speed at 3.2s
- **Best accuracy**: **Gemini 3 Flash Preview** — 69% accuracy, best item matching (96%), but 10x cost
- **Fastest**: **Qwen3.5 Flash** — 64% accuracy, fastest at 1.9s avg, cheapest at $0.13/1000 docs

### When to Use Which
| Scenario | Recommended Model | Why |
|----------|------------------|-----|
| High-volume receipt processing | Gemini 2.5 FL or Qwen3.5 Flash | <$0.13/1000 docs |
| Maximum accuracy needed | Gemini 3 Flash | 96% item matching |
| Latency-sensitive | Qwen3.5 Flash | 1.9s avg |
| Budget-constrained | Qwen3.5 Flash | Cheapest, fast |

### For Benchmark Improvement
1. **Increase to 100+ samples** — 50 is better but still has variance
2. **Add item modifier handling** — normalize `+` and `++` in ground truth names
3. **Add diverse document types** — invoices, forms, not just receipts
4. **Test with relaxed schema** to see if models extract more optional fields voluntarily
5. **Run on dev/test splits** — 100 dev + 100 test samples available

---

## Methodology

- **Dataset**: CORD train split, first 50 samples (receipt_00000 – receipt_00049)
- **Total items across 50 samples**: 139
- **Schema**: `{total: number, items: [{name: string, price: number, quantity: number}]}` with required fields
- **Structured output**: JSON Schema enforcement on all providers
  - OpenRouter: `response_format: {type: "json_schema", json_schema: {...}, strict: true}`
  - Gemini: `responseMimeType: "application/json"` + `responseSchema: {...}`
- **Scoring v2**:
  - Field-level comparison with normalized strings (space/hyphen/underscore insensitive)
  - Numeric comparison with 1% tolerance
  - Date parsing and normalization
  - Item matching: name-weighted (60%) with best-match bipartite assignment
  - Only expected fields are scored (extra fields in actual don't penalize)
