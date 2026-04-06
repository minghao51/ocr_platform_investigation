from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from auth import create_access_token
from main import app

client = TestClient(app)


def get_auth_header():
    token = create_access_token(user_id=1, username="test_user", is_admin=True)
    return {"Authorization": f"Bearer {token}"}


def test_list_benchmark_runs_passes_filters_to_crud():
    mock_runs = [{"id": 1, "dataset": "cord", "provider": "gemini"}]

    with patch("routers.benchmarks.crud.list_benchmark_runs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_runs

        response = client.get(
            "/api/benchmarks/runs?limit=25&dataset=cord&provider=gemini",
            headers=get_auth_header(),
        )

        assert response.status_code == 200
        assert response.json() == mock_runs
        mock_list.assert_awaited_once_with(limit=25, dataset="cord", provider="gemini")


def test_compare_models_returns_latest_run_per_model_and_respects_limit():
    mock_runs = [
        {
            "id": 5,
            "dataset": "cord",
            "provider": "gemini",
            "model": "gemini-2.5-flash-lite",
            "sample_count": 50,
            "overall_accuracy": 0.61,
            "avg_latency": 2.8,
            "total_cost": 0.01,
            "total_prompt_tokens": 100,
            "total_completion_tokens": 50,
            "success_rate": 0.6,
            "started_at": "2026-04-06 10:00:00",
        },
        {
            "id": 4,
            "dataset": "cord",
            "provider": "gemini",
            "model": "gemini-2.5-flash-lite",
            "sample_count": 20,
            "overall_accuracy": 0.75,
            "avg_latency": 2.5,
            "total_cost": 0.02,
            "total_prompt_tokens": 80,
            "total_completion_tokens": 40,
            "success_rate": 0.8,
            "started_at": "2026-04-05 10:00:00",
        },
        {
            "id": 3,
            "dataset": "cord",
            "provider": "openrouter",
            "model": "qwen/qwen3.5-flash-02-23",
            "sample_count": 20,
            "overall_accuracy": 0.7,
            "avg_latency": 1.9,
            "total_cost": 0.005,
            "total_prompt_tokens": 90,
            "total_completion_tokens": 45,
            "success_rate": 0.7,
            "started_at": "2026-04-05 09:00:00",
        },
    ]

    with patch("routers.benchmarks.crud.list_benchmark_runs", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_runs

        response = client.get(
            "/api/benchmarks/compare?dataset=cord&limit=1",
            headers=get_auth_header(),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) == 1
        assert data["runs"][0]["run_id"] == 3
        mock_list.assert_awaited_once_with(limit=500, dataset="cord")
