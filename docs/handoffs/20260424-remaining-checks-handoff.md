# Remaining Checks Handoff (2026-04-24)

## Context
Recent stabilization work was completed for:
- processing worker kwarg mismatch
- schema suggestion history auth enforcement
- backend jobs `offset` support
- benchmark docling-parse semaphore usage
- upload contract test alignment

Verification completed after those fixes:
- Backend: `uv run pytest tests/ -q` -> `201 passed, 9 skipped`
- Frontend: `npm run check` -> pass
- Frontend: `npm test` -> pass

## Remaining Issues and Concerns

### 1. `analyze-pdf` access control gap (security)
- Endpoint currently does not verify file ownership/guest token before returning PDF analysis metadata.
- File: `backend/routers/upload.py` (`/api/upload/analyze-pdf/{file_id}`)
- Concern: a guessed `file_id` may leak file existence and text-layer characteristics.
- Suggested fix:
  - Add `request: Request` and `current_user: dict | None = Depends(get_optional_user)`.
  - Reuse `ensure_file_access(file_record, current_user, request.headers.get("X-Guest-Token"))` before analysis.

### 2. Auto method vs provider requirement mismatch (UX/API contract)
- Frontend does not require provider/model when extraction method is `auto`.
- Backend may resolve `auto` to a provider-backed method and then reject when provider/model are missing.
- Files:
  - `frontend/src/pages/BaseExtractionPage.tsx`
  - `frontend/src/components/MethodModelSelector.tsx`
  - `backend/routers/processing.py`
- Concern: user can click Process in `auto` mode and receive 400 despite valid file.
- Suggested fix options (pick one and apply consistently):
  - Option A: Treat `auto` as provider-required in UI.
  - Option B: Backend applies default provider/model when `auto` picks provider-backed methods.
  - Option C: Restrict `auto` to local-only paths unless provider/model are supplied.

### 3. History pagination is still partial (product gap)
- Backend now supports `offset`, but UI currently always queries first page (`PAGE_SIZE + 1`) and only shows a refresh button.
- File: `frontend/src/pages/HistoryPage.tsx`
- Concern: users cannot actually navigate older pages.
- Suggested fix:
  - Track `offset` in component state.
  - Add `Load more` behavior calling `listJobs(..., PAGE_SIZE + 1, offset)`.
  - Maintain deduped append and `hasMore` handling.

### 4. Dead/unreachable exception handling in docling-parse path (maintainability/risk)
- `_process_via_docling_parse` has `except Exception` followed by `except ValueError` and another `except Exception`.
- File: `backend/services/processing.py`
- Concern: intended specialized error handling is unreachable and confusing for future modifications.
- Suggested fix:
  - Collapse into one coherent exception block or order from specific to general.

### 5. Provider catalog drift between config and runtime lists (consistency)
- `providers.yaml` contains model IDs not present in runtime provider classes, and vice versa.
- Files:
  - `backend/config/providers.yaml`
  - `backend/services/gemini.py`
  - `backend/services/openrouter.py`
- Concern: inconsistent fallback model lists and stale docs/UX when provider key is unavailable.
- Suggested fix:
  - Decide source of truth (`providers.yaml` or provider class lists).
  - Add lightweight test asserting configured IDs are subset of runtime IDs (or vice versa, per policy).

## Test and Validation Tasks for Next Agent

1. Security tests
- Add integration tests to ensure `/api/upload/analyze-pdf/{file_id}` respects user/guest access boundaries.

2. Auto-mode behavioral tests
- Add integration coverage for:
  - `auto` with no provider/model for PDF that routes to provider-backed method.
  - `auto` with provider/model present.
  - `auto` for image/audio paths.

3. Pagination behavior tests
- Add frontend unit/e2e checks validating `Load more`/offset behavior in history.

4. Benchmark warning follow-up
- Investigate warning seen in backend tests:
  - `tests/integration/test_benchmark_runner.py::TestRunBenchmark::test_concurrency_limit`
  - warning: coroutine `AsyncMockMixin._execute_mock_call` was never awaited.
- Ensure async mocks are awaited correctly in concurrency tests.

5. Existing skipped tests review
- Review skipped transcription and docling fixture-dependent tests and determine if they should remain skipped or be made deterministic.

## Suggested Execution Order
1. Fix `analyze-pdf` auth first.
2. Resolve `auto` method/provider contract.
3. Implement usable history pagination UI.
4. Clean exception blocks in processing service.
5. Align provider catalogs and add guard tests.
6. Re-run full test suite and frontend checks.

## Commands
- Backend full tests: `uv run pytest tests/ -q`
- Frontend checks: `npm run check`
- Frontend tests: `npm test`
