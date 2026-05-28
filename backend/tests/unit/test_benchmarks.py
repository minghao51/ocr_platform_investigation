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

    with patch(
        "routers.benchmarks.crud.list_benchmark_runs", new_callable=AsyncMock
    ) as mock_list:
        mock_list.return_value = mock_runs

        response = client.get(
            "/api/benchmarks/runs?limit=25&dataset=cord&provider=gemini",
            headers=get_auth_header(),
        )

        assert response.status_code == 200
        assert response.json() == mock_runs
        mock_list.assert_awaited_once_with(limit=25, dataset="cord", provider="gemini")


def test_compare_models_returns_latest_run_per_model_and_respects_limit():
    mock_comparison = [
        {
            "provider": "openrouter",
            "model": "qwen/qwen3.5-flash-02-23",
            "processing_method": "vision",
            "avg_accuracy": 0.7,
            "run_count": 1,
        },
        {
            "provider": "gemini",
            "model": "gemini-2.5-flash-lite",
            "processing_method": "vision",
            "avg_accuracy": 0.61,
            "run_count": 2,
        },
    ]

    with patch(
        "routers.benchmarks.crud.get_model_comparison", new_callable=AsyncMock
    ) as mock_compare:
        mock_compare.return_value = mock_comparison

        response = client.get(
            "/api/benchmarks/compare?dataset=cord&limit=1",
            headers=get_auth_header(),
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) == 1
        assert data["runs"][0]["provider"] == "openrouter"
        mock_compare.assert_awaited_once_with(dataset="cord", limit=1)
