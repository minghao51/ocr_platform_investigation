"""
Integration tests for benchmark CRUD operations.
"""

import pytest
import pytest_asyncio

from database.pool import connect
from database import crud
from database.migrations import run_migrations


@pytest_asyncio.fixture
async def clean_db(tmp_path, monkeypatch):
    db_path = tmp_path / "bench_crud.db"
    monkeypatch.setattr("database.pool.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.migrations.get_db_path", lambda: db_path)
    monkeypatch.setattr("dependencies._get_cached_db_path", lambda: db_path)

    await run_migrations()

    yield

    async with connect() as db:
        await db.execute(
            "DELETE FROM benchmark_results WHERE run_id IN (SELECT id FROM benchmark_runs WHERE dataset LIKE 'test_%')"
        )
        await db.execute("DELETE FROM benchmark_runs WHERE dataset LIKE 'test_%'")
        await db.commit()


class TestCreateBenchmarkRun:
    """Test creating benchmark runs."""

    @pytest.mark.asyncio
    async def test_create_run_basic(self, clean_db):
        """Test creating a basic benchmark run."""
        run_id = await crud.create_benchmark_run(
            dataset="test_basic",
            provider="test_provider",
            model="test-model",
            sample_count=10,
        )

        assert run_id is not None
        assert isinstance(run_id, int)

        # Verify the run was created
        run = await crud.get_benchmark_run(run_id)
        assert run is not None
        assert run["dataset"] == "test_basic"
        assert run["provider"] == "test_provider"
        assert run["model"] == "test-model"
        assert run["sample_count"] == 10

    @pytest.mark.asyncio
    async def test_create_multiple_runs(self, clean_db):
        """Test creating multiple benchmark runs."""
        run_id_1 = await crud.create_benchmark_run(
            dataset="test_multi_1",
            provider="provider_a",
            model="model-1",
            sample_count=5,
        )
        run_id_2 = await crud.create_benchmark_run(
            dataset="test_multi_2",
            provider="provider_b",
            model="model-2",
            sample_count=10,
        )

        assert run_id_1 != run_id_2

        # Verify both exist
        run_1 = await crud.get_benchmark_run(run_id_1)
        run_2 = await crud.get_benchmark_run(run_id_2)

        assert run_1["model"] == "model-1"
        assert run_2["model"] == "model-2"


class TestAddBenchmarkResult:
    """Test adding benchmark results."""

    @pytest.mark.asyncio
    async def test_add_result_basic(self, clean_db):
        """Test adding a basic benchmark result."""
        run_id = await crud.create_benchmark_run(
            dataset="test_result_basic",
            provider="test_provider",
            model="test-model",
            sample_count=1,
        )

        await crud.add_benchmark_result(
            run_id=run_id,
            sample_index=0,
            file_path="/fake/path/image.png",
            accuracy_score=0.85,
            latency=2.5,
            cost=0.001,
            prompt_tokens=500,
            completion_tokens=200,
            expected_json='{"total": 100}',
            actual_json='{"total": 100}',
            field_scores='{"total": {"score": 1.0}}',
        )

        # Verify the result was added
        results = await crud.get_benchmark_results(run_id)
        assert len(results) == 1
        assert results[0]["sample_index"] == 0
        assert results[0]["accuracy_score"] == 0.85
        assert results[0]["latency"] == 2.5

    @pytest.mark.asyncio
    async def test_add_result_with_error(self, clean_db):
        """Test adding a result with an error message."""
        run_id = await crud.create_benchmark_run(
            dataset="test_result_error",
            provider="test_provider",
            model="test-model",
            sample_count=1,
        )

        await crud.add_benchmark_result(
            run_id=run_id,
            sample_index=0,
            file_path="/fake/path/image.png",
            accuracy_score=0.0,
            latency=1.0,
            cost=0.0,
            prompt_tokens=0,
            completion_tokens=0,
            error_message="API rate limit exceeded",
        )

        results = await crud.get_benchmark_results(run_id)
        assert len(results) == 1
        assert results[0]["accuracy_score"] == 0.0
        assert results[0]["error_message"] == "API rate limit exceeded"


class TestUpdateBenchmarkRun:
    """Test updating benchmark runs with aggregated metrics."""

    @pytest.mark.asyncio
    async def test_update_run_metrics(self, clean_db):
        """Test updating a run with completion metrics."""
        run_id = await crud.create_benchmark_run(
            dataset="test_update",
            provider="test_provider",
            model="test-model",
            sample_count=10,
        )

        await crud.update_benchmark_run(
            run_id=run_id,
            overall_accuracy=0.75,
            avg_latency=3.2,
            total_cost=0.015,
            total_prompt_tokens=5000,
            total_completion_tokens=2000,
        )

        # Verify the update
        run = await crud.get_benchmark_run(run_id)
        assert run["overall_accuracy"] == 0.75
        assert run["avg_latency"] == 3.2
        assert run["total_cost"] == 0.015
        assert run["total_prompt_tokens"] == 5000
        assert run["total_completion_tokens"] == 2000
        assert run["completed_at"] is not None


class TestListBenchmarkRuns:
    """Test listing benchmark runs with filters."""

    @pytest.mark.asyncio
    async def test_list_all_runs(self, clean_db):
        """Test listing all benchmark runs."""
        await crud.create_benchmark_run("test_list_1", "prov_a", "model-1", 10)
        await crud.create_benchmark_run("test_list_2", "prov_b", "model-2", 20)
        await crud.create_benchmark_run("test_list_3", "prov_a", "model-3", 15)

        runs = await crud.list_benchmark_runs(limit=10)
        # Filter for test datasets only
        test_runs = [r for r in runs if r["dataset"].startswith("test_list_")]
        assert len(test_runs) == 3

    @pytest.mark.asyncio
    async def test_list_by_dataset(self, clean_db):
        """Test filtering by dataset."""
        await crud.create_benchmark_run("test_filter_cord", "prov_a", "model-1", 10)
        await crud.create_benchmark_run("test_filter_other", "prov_b", "model-2", 20)

        runs = await crud.list_benchmark_runs(dataset="test_filter_cord", limit=10)
        assert len(runs) >= 1
        assert all(r["dataset"] == "test_filter_cord" for r in runs)

    @pytest.mark.asyncio
    async def test_list_by_provider(self, clean_db):
        """Test filtering by provider."""
        await crud.create_benchmark_run("test_prov_1", "provider_a", "model-1", 10)
        await crud.create_benchmark_run("test_prov_2", "provider_b", "model-2", 20)
        await crud.create_benchmark_run("test_prov_3", "provider_a", "model-3", 15)

        runs = await crud.list_benchmark_runs(provider="provider_a", limit=10)
        # Filter for test datasets only
        test_runs = [r for r in runs if r["dataset"].startswith("test_prov_")]
        assert len(test_runs) == 2
        assert all(r["provider"] == "provider_a" for r in test_runs)

    @pytest.mark.asyncio
    async def test_limit_respected(self, clean_db):
        """Test that limit parameter is respected."""
        for i in range(5):
            await crud.create_benchmark_run(f"test_limit_{i}", "prov", "model", 10)

        runs = await crud.list_benchmark_runs(limit=3)
        test_runs = [r for r in runs if r["dataset"].startswith("test_limit_")]
        assert len(test_runs) <= 3


class TestGetBenchmarkRun:
    """Test retrieving individual benchmark runs."""

    @pytest.mark.asyncio
    async def test_get_existing_run(self, clean_db):
        """Test getting an existing benchmark run."""
        run_id = await crud.create_benchmark_run(
            dataset="test_get",
            provider="test_provider",
            model="test-model",
            sample_count=10,
        )

        run = await crud.get_benchmark_run(run_id)
        assert run is not None
        assert run["id"] == run_id
        assert run["dataset"] == "test_get"

    @pytest.mark.asyncio
    async def test_get_nonexistent_run(self, clean_db):
        """Test getting a run that doesn't exist."""
        run = await crud.get_benchmark_run(99999)
        assert run is None


class TestGetBenchmarkResults:
    """Test retrieving results for a benchmark run."""

    @pytest.mark.asyncio
    async def test_get_results_for_run(self, clean_db):
        """Test getting all results for a benchmark run."""
        run_id = await crud.create_benchmark_run(
            dataset="test_results",
            provider="test_provider",
            model="test-model",
            sample_count=3,
        )

        # Add multiple results
        for i in range(3):
            await crud.add_benchmark_result(
                run_id=run_id,
                sample_index=i,
                file_path=f"/fake/path/image_{i}.png",
                accuracy_score=0.8 + i * 0.05,
                latency=2.0 + i,
                cost=0.001 * (i + 1),
                prompt_tokens=500,
                completion_tokens=200,
            )

        results = await crud.get_benchmark_results(run_id)
        assert len(results) == 3
        assert results[0]["sample_index"] == 0
        assert results[1]["sample_index"] == 1
        assert results[2]["sample_index"] == 2

    @pytest.mark.asyncio
    async def test_get_results_empty(self, clean_db):
        """Test getting results for a run with no results."""
        run_id = await crud.create_benchmark_run(
            dataset="test_empty",
            provider="test_provider",
            model="test-model",
            sample_count=0,
        )

        results = await crud.get_benchmark_results(run_id)
        assert len(results) == 0


class TestGetModelComparison:
    """Test benchmark comparison aggregation."""

    @pytest.mark.asyncio
    async def test_get_model_comparison_returns_latest_run_per_combo(self, clean_db):
        older_run = await crud.create_benchmark_run(
            dataset="test_compare",
            provider="gemini",
            model="gemini-2.5-flash",
            sample_count=2,
            processing_method="vision",
        )
        await crud.add_benchmark_result(
            run_id=older_run,
            sample_index=0,
            accuracy_score=0.25,
            latency=1.5,
            cost=0.01,
        )
        await crud.update_benchmark_run(
            run_id=older_run,
            overall_accuracy=0.25,
            avg_latency=1.5,
            total_cost=0.01,
            total_prompt_tokens=100,
            total_completion_tokens=50,
        )

        newer_run = await crud.create_benchmark_run(
            dataset="test_compare",
            provider="gemini",
            model="gemini-2.5-flash",
            sample_count=3,
            processing_method="vision",
        )
        await crud.add_benchmark_result(
            run_id=newer_run,
            sample_index=0,
            accuracy_score=0.75,
            latency=0.8,
            cost=0.02,
        )
        await crud.update_benchmark_run(
            run_id=newer_run,
            overall_accuracy=0.75,
            avg_latency=0.8,
            total_cost=0.02,
            total_prompt_tokens=200,
            total_completion_tokens=100,
        )

        hybrid_run = await crud.create_benchmark_run(
            dataset="test_compare",
            provider="gemini",
            model="gemini-2.5-flash",
            sample_count=1,
            processing_method="hybrid",
        )
        await crud.add_benchmark_result(
            run_id=hybrid_run,
            sample_index=0,
            accuracy_score=0.6,
            latency=1.0,
            cost=0.03,
        )
        await crud.update_benchmark_run(
            run_id=hybrid_run,
            overall_accuracy=0.6,
            avg_latency=1.0,
            total_cost=0.03,
            total_prompt_tokens=150,
            total_completion_tokens=75,
        )

        comparison = await crud.get_model_comparison(dataset="test_compare", limit=10)

        assert {row["run_id"] for row in comparison} == {newer_run, hybrid_run}
        assert all(row["provider"] == "gemini" for row in comparison)
        assert all(row["model"] == "gemini-2.5-flash" for row in comparison)
        assert all(row["sample_count"] in {1, 3} for row in comparison)
        assert all(
            row["processing_method"] in {"vision", "hybrid"} for row in comparison
        )
