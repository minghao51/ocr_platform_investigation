# Implementation Plan: Benchmark & Cost Performance

> Created: 2026-04-04
> Status: In Progress
> Scope: Phase 1 (Cost Tracking) + Phase 2 (Benchmark Framework) + Phase 3 (Structured Output)

## Overview

Add cost tracking to every processing job and build a benchmark framework using the CORD receipt dataset from Hugging Face to compare provider/model accuracy, latency, and cost.

---

## Phase 1: Cost Tracking (COMPLETED)

### 1.1 DB Migration

Add columns to `processing_jobs`:
- `prompt_tokens INTEGER` — input tokens consumed
- `completion_tokens INTEGER` — output tokens consumed
- `total_tokens INTEGER` — sum of prompt + completion
- `estimated_cost REAL` — calculated cost in USD

### 1.2 Pricing Module (`backend/services/pricing.py`)

Per-model pricing dictionary with 2026 rates:
- Nebius: Qwen2.5-VL-72B
- OpenRouter: Claude 3.5 Sonnet, Gemini Pro 1.5, GPT-4o, Llama 3.2 90B Vision
- Gemini: gemini-3-pro-preview, gemini-3-flash-preview, gemini-2.5-pro, gemini-2.5-flash, gemini-2.5-flash-lite, gemini-2.0-flash

Function: `calculate_cost(provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> float`

### 1.3 Capture Token Usage

- Modify `update_job_status_with_broadcast()` in `processing.py` to accept `usage: dict` parameter
- Thread `usage` from provider responses through the processing pipeline
- Both `run_processing_job()` and `run_text_processing_job()` extract usage from provider result
- Calculate cost via pricing module before DB write

### 1.4 Serialize Cost

Add to `serialize_job()` in `routers/job_serialization.py`:
- `prompt_tokens`
- `completion_tokens`
- `estimated_cost`

---

## Phase 2: Benchmark Framework (COMPLETED)

### 2.1 Dataset Adapter (`backend/benchmarks/datasets.py`)

- Download CORD dataset from Hugging Face (`katanaml/cord`)
- Convert CORD annotation format to our schema:
  - Each sample: image path + expected fields (items, prices, totals, dates, vendor)
  - Generate JSON schema dynamically from CORD entity types
- Cache downloaded data in `data/benchmarks/cord/`
- Expose `load_cord_samples(limit=None) -> list[BenchmarkSample]`

### 2.2 Accuracy Scoring (`backend/benchmarks/scoring.py`)

Field-level comparison with smart matching:
- **Exact match**: IDs, vendor names, categorical fields
- **Normalized numeric**: amounts within 1% tolerance (handles rounding differences)
- **Date parsing**: normalize both values before comparing
- **Fuzzy string**: Levenshtein ratio > 0.85 for free-text fields

Returns:
- Per-field scores (dict of field_name -> score 0-1)
- Overall score (weighted average)

### 2.3 Benchmark Runner (`backend/benchmarks/runner.py`)

Core execution engine:
1. Load dataset samples
2. For each sample, run through specified provider/model
3. Parse output JSON, compare against ground truth
4. Record: accuracy per field, latency, cost, tokens, success/failure
5. Aggregate results

### 2.4 Results Storage

New tables in schema:

**`benchmark_runs`**:
- `id INTEGER PRIMARY KEY`
- `dataset TEXT` — e.g. "cord"
- `provider TEXT`
- `model TEXT`
- `sample_count INTEGER`
- `overall_accuracy REAL`
- `avg_latency REAL`
- `total_cost REAL`
- `total_prompt_tokens INTEGER`
- `total_completion_tokens INTEGER`
- `started_at TIMESTAMP`
- `completed_at TIMESTAMP`

**`benchmark_results`**:
- `id INTEGER PRIMARY KEY`
- `run_id INTEGER` (FK → benchmark_runs)
- `sample_index INTEGER`
- `file_path TEXT`
- `accuracy_score REAL`
- `latency REAL`
- `cost REAL`
- `prompt_tokens INTEGER`
- `completion_tokens INTEGER`
- `expected_json TEXT`
- `actual_json TEXT`
- `field_scores TEXT` — JSON of per-field scores
- `error_message TEXT`

### 2.5 CLI Commands

Add to `backend/cli.py`:
- `run-benchmark` — execute a benchmark run
  - `--provider` (required)
  - `--model` (required)
  - `--dataset` (default: "cord")
  - `--limit` (default: 20, max samples to process)
  - `--schema-id` (optional, use existing schema)
- `list-benchmarks` — show past benchmark runs with summary
- `show-benchmark <id>` — detailed results for a specific run

---

## Phase 3: Structured Output Enforcement

### Problem

Each provider currently relies on prompt engineering ("Respond ONLY with valid JSON") for structured output. No actual schema enforcement is used. This leads to:
- Inconsistent JSON structure
- Missing or extra fields
- Parsing failures
- Lower benchmark accuracy

### 3.1 Nebius (OpenAI-compatible endpoint)

**Current:** `response_format: {"type": "json_object"}`
**Fix:** Upgrade to `response_format: {"type": "json_schema", "json_schema": {"name": "extraction", "strict": true, "schema": {...}}}`

### 3.2 Gemini (native REST)

**Current:** `responseMimeType: "application/json"`
**Fix:** Add `responseSchema` to `generationConfig` with full JSON Schema

### 3.3 OpenRouter (OpenAI-compatible)

**Current:** No structured output at all
**Fix:** Add `response_format: {"type": "json_schema", "json_schema": {"name": "extraction", "strict": true, "schema": {...}}}`

### 3.4 Update Pricing Module

Add new models:
- OpenRouter: `qwen/qwen3.6-plus:free`, `qwen/qwen3.5-flash-02-23`, `google/gemini-2.5-flash-lite`, `google/gemini-2.5-flash`, `google/gemini-3-flash-preview`, `x-ai/grok-4.1-fast`, `openai/gpt-4.1-mini`
- Update OpenRouter model list in `get_models()`

---

## File Changes

### New Files
- `backend/services/pricing.py`
- `backend/benchmarks/__init__.py`
- `backend/benchmarks/datasets.py`
- `backend/benchmarks/scoring.py`
- `backend/benchmarks/runner.py`

### Modified Files
- `backend/database/schema.sql` — new columns + tables
- `backend/database/migrations.py` — migration for new columns/tables
- `backend/database/crud.py` — benchmark CRUD, updated `update_job_status`
- `backend/services/processing.py` — thread usage through pipeline
- `backend/routers/job_serialization.py` — add cost fields
- `backend/cli.py` — benchmark commands
- `backend/services/nebius.py` — structured output via json_schema
- `backend/services/gemini.py` — structured output via responseSchema
- `backend/services/openrouter.py` — structured output via json_schema
- `backend/services/pricing.py` — add new models

---

## Out of Scope (Future Phases)

- Phase 4: Provider pricing metadata in `/api/providers` endpoint
- Phase 5: Benchmark dashboard UI (`/benchmarks` route)
- OmniDocBench support (larger dataset, PDFs)
- LLM-as-judge accuracy scoring
