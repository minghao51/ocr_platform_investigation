from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from main import app
from auth import create_access_token
import pytest

client = TestClient(app)


def get_auth_header():
    """Get authorization header with test token."""
    token = create_access_token(user_id=1, username="test_user", is_admin=True)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_job_status_parses_result():
    mock_job = {
        "id": 123,
        "status": "success",
        "result": '{"invoice_number": "IVO-999", "total": 500}',
        "error_message": None,
        "processing_time_seconds": 1.2,
        "file_name": "test.jpg",
        "file_type": "jpg",
        "provider": "openrouter",
        "model": "llama",
        "schema_name": "Invoice",
        "created_at": "2026-01-01 00:00:00",
    }

    with patch("database.crud.get_job", new_callable=AsyncMock) as mock_get_job:
        mock_get_job.return_value = mock_job

        response = client.get("/api/process/status/123", headers=get_auth_header())

        assert response.status_code == 200
        data = response.json()

        # KEY CHECK: "result" should be a dict, not a string
        assert isinstance(data["result"], dict), (
            f"Expected dict, got {type(data['result'])}"
        )
        assert data["result"]["invoice_number"] == "IVO-999"
