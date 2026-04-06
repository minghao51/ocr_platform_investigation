from fastapi import APIRouter, HTTPException
from typing import Optional
from database import crud

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


@router.get("/runs")
async def list_benchmark_runs(
    limit: int = 50,
    dataset: Optional[str] = None,
    provider: Optional[str] = None,
):
    """List benchmark runs with optional filters."""
    limit = max(1, min(limit, 200))
    return await crud.list_benchmark_runs(
        limit=limit,
        dataset=dataset,
        provider=provider,
    )


@router.get("/runs/{run_id}")
async def get_benchmark_run(run_id: int):
    """Get a benchmark run by ID."""
    run = await crud.get_benchmark_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    return run


@router.get("/runs/{run_id}/results")
async def get_benchmark_results(run_id: int):
    """Get all results for a benchmark run."""
    run = await crud.get_benchmark_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Benchmark run not found")
    results = await crud.get_benchmark_results(run_id)
    return results


@router.get("/compare")
async def compare_models(
    dataset: str = "cord",
    limit: int = 20,
):
    """Get comparison of all models on a dataset."""
    limit = max(1, min(limit, 200))
    runs = await crud.list_benchmark_runs(limit=500, dataset=dataset)
    dataset_runs = [
        r for r in runs if r.get("overall_accuracy") is not None
    ]

    if not dataset_runs:
        return {"message": "No benchmark data available", "runs": []}

    latest_by_model = {}
    for run in dataset_runs:
        key = (run["provider"], run["model"])
        if key not in latest_by_model:
            latest_by_model[key] = run

    comparison = []
    for run in latest_by_model.values():
        comparison.append({
            "run_id": run["id"],
            "provider": run["provider"],
            "model": run["model"],
            "sample_count": run["sample_count"],
            "overall_accuracy": run["overall_accuracy"],
            "avg_latency": run["avg_latency"],
            "total_cost": run["total_cost"],
            "total_prompt_tokens": run["total_prompt_tokens"],
            "total_completion_tokens": run["total_completion_tokens"],
            "success_rate": run.get("success_rate"),
            "started_at": run.get("started_at"),
        })

    comparison.sort(key=lambda x: x["overall_accuracy"], reverse=True)
    return {"runs": comparison[:limit]}
