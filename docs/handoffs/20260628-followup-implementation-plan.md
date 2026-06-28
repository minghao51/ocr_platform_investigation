# Follow-Up Implementation Plan (2026-06-28)

## Completed in this pass

1. Removed the broken audio upload path from current backend and frontend product surfaces.
2. Closed the benchmark-access UX gap with route-level admin gating.
3. Fixed the repo's backend test command guidance.
4. Replaced one misleading skipped transcription test with deterministic current-behavior coverage.

## Recommended next tasks

1. Audit historical docs for drift.
   Focus on archived handoffs, manual checklists, and older API snapshots that still describe audio as live.

2. Decide on the future of audio explicitly.
   Option A: keep it out of scope and remove remaining backend-only references.
   Option B: build a real audio ingestion and provider-backed transcription path, then re-enable upload support with tests.

3. Add targeted regression coverage where the repo has infrastructure for it.
   Best next addition: a frontend route test or e2e assertion that non-admin users cannot stay on `/benchmarks`.

## Resume commands

```bash
cd backend
uv run pytest tests/

cd ../frontend
npm run check
npm test
```
