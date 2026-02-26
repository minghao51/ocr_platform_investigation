from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from main import app
import pytest

client = TestClient(app)


@pytest.mark.asyncio
async def test_get_job_status_parses_result():
    mock_job = {
        "id": 123,
        "status": "success",
        "result": '{"invoice_number": "IVO-999", "total": 500}',  # JSON string from DB
        "error_message": None,
        "processing_time_seconds": 1.2,
    }

    with patch("database.crud.get_job", new_callable=AsyncMock) as mock_get_job:
        mock_get_job.return_value = mock_job

        response = client.get("/api/process/status/123")

        assert response.status_code == 200
        data = response.json()

        # KEY CHECK: "result" should be a dict, not a string
        assert isinstance(data["result"], dict), (
            f"Expected dict, got {type(data['result'])}"
        )
        assert data["result"]["invoice_number"] == "IVO-999"
