from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from database import crud
from dependencies import require_admin

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.get("/runs")
async def list_benchmark_runs(
    limit: int = 50,
    dataset: Optional[str] = None,
    provider: Optional[str] = None,
    current_user: dict = Depends(require_admin),
):
    """List benchmark runs with optional filters."""
    _ = current_user
    limit = max(1, min(limit, 200))
    return await crud.list_benchmark_runs(
        limit=limit,
        dataset=dataset,
        provider=provider,
    )


@router.get("/runs/{run_id}")
async def get_benchmark_run(
    run_id: int,
    current_user: dict = Depends(require_admin),
):
    """Get a benchmark run by ID."""
    _ = current_user
    run = await crud.get_benchmark_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    return run


@router.get("/runs/{run_id}/results")
async def get_benchmark_results(
    run_id: int,
    current_user: dict = Depends(require_admin),
):
    """Get all results for a benchmark run."""
    _ = current_user
    run = await crud.get_benchmark_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    results = await crud.get_benchmark_results(run_id)
    return results


@router.get("/compare")
async def compare_models(
    dataset: str = "cord",
    limit: int = 20,
    current_user: dict = Depends(require_admin),
):
    """Get comparison of all models on a dataset."""
    _ = current_user
    limit = max(1, min(limit, 200))
    comparison = await crud.get_model_comparison(dataset=dataset, limit=limit)

    if not comparison:
        return {"message": "No benchmark data available", "runs": []}

    runs = []
    for row in comparison:
        runs.append(
            {
                "provider": row["provider"],
                "model": row["model"],
                "processing_method": "vision",
                "sample_count": None,
                "overall_accuracy": row["avg_accuracy"],
                "avg_latency": None,
                "total_cost": None,
                "total_prompt_tokens": None,
                "total_completion_tokens": None,
                "success_rate": None,
                "started_at": None,
            }
        )

    return {"runs": runs[:limit]}


@router.get("/models")
async def get_benchmarked_models(
    current_user: dict = Depends(require_admin),
):
    """Return all provider/model combos that have benchmark data."""
    _ = current_user
    return await crud.get_benchmarked_models_summary()
