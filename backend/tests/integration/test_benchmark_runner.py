"""
Integration tests for benchmark runner.
Tests the full benchmark execution flow with mocked VLM responses.
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch

from benchmarks.runner import run_benchmark, _process_single_sample
from database.pool import connect
from database.migrations import run_migrations


@pytest_asyncio.fixture
async def clean_db(tmp_path, monkeypatch):
    db_path = tmp_path / "bench_runner.db"
    monkeypatch.setattr("database.pool.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.migrations._get_db_path", lambda: db_path)
    monkeypatch.setattr("dependencies._get_cached_db_path", lambda: db_path)

    await run_migrations()

    yield

    async with connect() as db:
        await db.execute(
            "DELETE FROM benchmark_results WHERE run_id IN (SELECT id FROM benchmark_runs WHERE dataset LIKE 'runner_test_%')"
        )
        await db.execute(
            "DELETE FROM benchmark_runs WHERE dataset LIKE 'runner_test_%'"
        )
        await db.commit()


class TestProcessSingleSample:
    """Test processing of individual benchmark samples."""

    @pytest.mark.asyncio
    async def test_successful_sample_processing(self, clean_db):
        """Test successful processing of a sample."""
        from tests.fixtures.benchmark_fixtures import (
            STANDARD_RECEIPT_SAMPLE,
            PERFECT_OUTPUT,
            create_mock_provider,
        )
        from PIL import Image
        import tempfile
        import os

        # Create a proper async semaphore mock
        import asyncio

        semaphore = asyncio.Semaphore(10)

        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
            Image.new("RGB", (100, 100), color="white").save(tmp_path)

        try:
            # Update the sample to use the real image path
            STANDARD_RECEIPT_SAMPLE.image_path = tmp_path

            mock_provider = create_mock_provider([PERFECT_OUTPUT])

            processing_service = MagicMock()
            processing_service.get_provider = MagicMock(return_value=mock_provider)
            processing_service.image_service = MagicMock()
            processing_service.image_service.resize_image = lambda img, size: img

            result = await _process_single_sample(
                idx=0,
                sample=STANDARD_RECEIPT_SAMPLE,
                provider_name="test_provider",
                model="test-model",
                api_key="test_key",
                prompt="Extract data",
                semaphore=semaphore,
                processing_service=processing_service,
            )

            assert result["sample_index"] == 0
            assert result["accuracy_score"] > 0.9  # Perfect match
            assert result["latency"] > 0
            # Cost might be 0 for test models without pricing
            assert result.get("error_message") is None  # No error
        finally:
            os.unlink(tmp_path)

    @pytest.mark.asyncio
    async def test_api_error_handling(self, clean_db):
        """Test handling of API errors."""
        from tests.fixtures.benchmark_fixtures import (
            STANDARD_RECEIPT_SAMPLE,
            ERROR_RESPONSE,
            create_mock_provider,
        )
        from PIL import Image

        # Create a proper async semaphore mock
        import asyncio

        semaphore = asyncio.Semaphore(10)

        # Create a fake image for the test
        fake_image = Image.new("RGB", (100, 100), color="white")

        mock_provider = create_mock_provider([ERROR_RESPONSE])

        processing_service = MagicMock()
        processing_service.get_provider = MagicMock(return_value=mock_provider)
        processing_service.image_service = MagicMock()
        processing_service.image_service.resize_image = lambda img, size: img

        # Mock Image.open to return our fake image
        with patch("PIL.Image.open", return_value=fake_image):
            result = await _process_single_sample(
                idx=0,
                sample=STANDARD_RECEIPT_SAMPLE,
                provider_name="test_provider",
                model="test-model",
                api_key="test_key",
                prompt="Extract data",
                semaphore=semaphore,
                processing_service=processing_service,
            )

        assert result["sample_index"] == 0
        assert result["accuracy_score"] == 0.0  # Error = 0 score
        assert "error" in result["error_message"].lower()

    @pytest.mark.asyncio
    async def test_cord_modifier_handling(self, clean_db):
        """Test that CORD modifiers are handled correctly."""
        from tests.fixtures.benchmark_fixtures import (
            CORD_MODIFIER_SAMPLE,
            CORD_MODIFIER_OUTPUT,
            create_mock_provider,
        )
        from PIL import Image

        # Create a proper async semaphore mock
        import asyncio

        semaphore = asyncio.Semaphore(10)

        # Create a fake image for the test
        fake_image = Image.new("RGB", (100, 100), color="white")

        mock_provider = create_mock_provider([CORD_MODIFIER_OUTPUT])

        processing_service = MagicMock()
        processing_service.get_provider = MagicMock(return_value=mock_provider)
        processing_service.image_service = MagicMock()
        processing_service.image_service.resize_image = lambda img, size: img

        # Mock Image.open to return our fake image
        with patch("PIL.Image.open", return_value=fake_image):
            result = await _process_single_sample(
                idx=0,
                sample=CORD_MODIFIER_SAMPLE,
                provider_name="test_provider",
                model="test-model",
                api_key="test_key",
                prompt="Extract data",
                semaphore=semaphore,
                processing_service=processing_service,
            )

        # Should have good score despite modifier difference
        assert result["accuracy_score"] > 0.5


class TestRunBenchmark:
    """Test the full benchmark run flow."""

    @pytest.mark.asyncio
    async def test_successful_run(self, clean_db):
        """Test a successful benchmark run with multiple samples."""
        from tests.fixtures.benchmark_fixtures import (
            get_all_fixture_samples,
            create_mock_provider,
        )
        from PIL import Image

        samples = get_all_fixture_samples()

        # Create a fake image for the test
        fake_image = Image.new("RGB", (100, 100), color="white")

        # Mock load_dataset to return our fixtures
        with patch("benchmarks.datasets_extended.load_dataset", return_value=samples):
            # Create mock responses for each sample
            mock_responses = [
                {
                    "content": '{"total": 25.50, "items": [{"name": "Coffee", "price": 4.5, "quantity": 2}]}',
                    "usage": {"prompt_tokens": 500, "completion_tokens": 200},
                }
            ] * len(samples)

            mock_provider = create_mock_provider(mock_responses)

            processing_service = MagicMock()
            processing_service.get_provider = MagicMock(return_value=mock_provider)
            processing_service.image_service = MagicMock()
            processing_service.image_service.resize_image = lambda img, size: img

            with patch(
                "services.processing.ProcessingService", return_value=processing_service
            ):
                with patch("benchmarks.runner.Image.open", return_value=fake_image):
                    summary = await run_benchmark(
                        provider_name="test_provider",
                        model="test-model",
                        api_key="test_key",
                        dataset="synthetic_invoice",
                        limit=len(samples),
                        concurrency=2,
                    )

        assert summary["run_id"] > 0
        assert summary["sample_count"] == len(samples)
        assert 0 <= summary["overall_accuracy"] <= 1
        assert summary["avg_latency"] > 0
        assert summary["total_cost"] >= 0

    @pytest.mark.asyncio
    async def test_concurrency_limit(self, clean_db):
        """Test that concurrency limit is respected."""
        from tests.fixtures.benchmark_fixtures import get_all_fixture_samples
        from PIL import Image
        import asyncio

        samples = get_all_fixture_samples()[:3]  # Use 3 samples

        # Create a fake image for the test
        fake_image = Image.new("RGB", (100, 100), color="white")

        # Track concurrent calls
        max_concurrent = 0
        current_concurrent = 0
        lock = asyncio.Lock()

        async def mock_process(*args, **kwargs):
            _ = args, kwargs  # Mark as intentionally unused
            nonlocal max_concurrent, current_concurrent
            async with lock:
                current_concurrent += 1
                max_concurrent = max(max_concurrent, current_concurrent)
            await asyncio.sleep(0.1)  # Simulate work
            async with lock:
                current_concurrent -= 1
            return {
                "content": '{"total": 100}',
                "usage": {"prompt_tokens": 500, "completion_tokens": 200},
            }

        with patch("benchmarks.datasets_extended.load_dataset", return_value=samples):
            mock_provider = MagicMock()
            mock_provider.get_default_image_size = MagicMock(return_value=(1024, 1024))
            mock_provider.process_image = mock_process

            processing_service = MagicMock()
            processing_service.get_provider = MagicMock(return_value=mock_provider)
            processing_service.image_service = MagicMock()
            processing_service.image_service.resize_image = lambda img, size: img

            with patch(
                "services.processing.ProcessingService", return_value=processing_service
            ):
                with patch("benchmarks.runner.Image.open", return_value=fake_image):
                    await run_benchmark(
                        provider_name="test_provider",
                        model="test-model",
                        api_key="test_key",
                        dataset="synthetic_invoice",
                        limit=len(samples),
                        concurrency=2,  # Max 2 concurrent
                    )

        # Should not exceed concurrency limit
        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(self, clean_db):
        """Test a run with both successful and failed samples."""
        from tests.fixtures.benchmark_fixtures import (
            get_all_fixture_samples,
            create_mock_provider,
        )
        from PIL import Image

        samples = get_all_fixture_samples()[:3]

        # Create a fake image for the test
        fake_image = Image.new("RGB", (100, 100), color="white")

        # Mix of success and error responses
        mock_responses = [
            {
                "content": '{"total": 100}',
                "usage": {"prompt_tokens": 500, "completion_tokens": 200},
            },
            {"error": "Rate limit exceeded", "usage": {}},
            {
                "content": '{"total": 200}',
                "usage": {"prompt_tokens": 500, "completion_tokens": 200},
            },
        ]

        with patch("benchmarks.datasets_extended.load_dataset", return_value=samples):
            mock_provider = create_mock_provider(mock_responses)

            processing_service = MagicMock()
            processing_service.get_provider = MagicMock(return_value=mock_provider)
            processing_service.image_service = MagicMock()
            processing_service.image_service.resize_image = lambda img, size: img

            with patch(
                "services.processing.ProcessingService", return_value=processing_service
            ):
                with patch("benchmarks.runner.Image.open", return_value=fake_image):
                    summary = await run_benchmark(
                        provider_name="test_provider",
                        model="test-model",
                        api_key="test_key",
                        dataset="synthetic_invoice",
                        limit=len(samples),
                        concurrency=2,
                    )

        # Overall accuracy should be lower due to error
        assert summary["overall_accuracy"] < 1.0
        # Success rate should reflect 2/3 successful
        assert summary["success_rate"] == 2 / 3

    @pytest.mark.asyncio
    async def test_empty_dataset(self, clean_db):
        """Test handling of empty dataset."""
        with patch("benchmarks.runner.load_dataset", return_value=[]):
            with pytest.raises(ValueError, match="No samples loaded"):
                await run_benchmark(
                    provider_name="test_provider",
                    model="test-model",
                    api_key="test_key",
                    dataset="synthetic_invoice",
                    limit=0,
                )
