import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_db(mocker):
    conn = AsyncMock()
    conn.__aenter__.return_value = conn
    conn.execute.return_value = AsyncMock()

    wrapper = mocker.patch("database.crud.jobs.connect", autospec=True)
    wrapper.return_value = conn
    return conn


class TestCreateJob:
    @pytest.mark.asyncio
    async def test_create_job_returns_id(self, mock_db):
        from database.crud.jobs import create_job

        mock_db.execute.return_value = AsyncMock(lastrowid=42)

        job_id = await create_job(
            file_name="test.pdf",
            file_type="pdf",
            provider="test_provider",
            model="test_model",
            schema_id=None,
            schema_name=None,
        )

        assert job_id == 42
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()


class TestGetJob:
    @pytest.mark.asyncio
    async def test_get_job_returns_dict(self, mock_db):
        from database.crud.jobs import get_job

        mock_db.row_factory = None
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {"id": 1, "status": "pending"}
        mock_db.execute.return_value = mock_cursor

        job = await get_job(1)
        assert job == {"id": 1, "status": "pending"}

    @pytest.mark.asyncio
    async def test_get_job_returns_none_when_missing(self, mock_db):
        from database.crud.jobs import get_job

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_db.execute.return_value = mock_cursor

        job = await get_job(999)
        assert job is None


class TestListJobs:
    @pytest.mark.asyncio
    async def test_list_jobs_no_filters(self, mock_db):
        from database.crud.jobs import list_jobs

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [
            {"id": 1, "status": "success"},
            {"id": 2, "status": "pending"},
        ]
        mock_db.execute.return_value = mock_cursor

        jobs = await list_jobs()
        assert len(jobs) == 2
        assert jobs[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_list_jobs_with_status_filter(self, mock_db):
        from database.crud.jobs import list_jobs

        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "status": "success"}]
        mock_db.execute.return_value = mock_cursor

        jobs = await list_jobs(status="success")
        assert len(jobs) == 1
        assert "success" in mock_db.execute.call_args[0][1]


class TestCountJobs:
    @pytest.mark.asyncio
    async def test_count_jobs_no_filters(self, mock_db):
        from database.crud.jobs import count_jobs

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = [42]
        mock_db.execute.return_value = mock_cursor

        count = await count_jobs()
        assert count == 42

    @pytest.mark.asyncio
    async def test_count_jobs_with_provider_filter(self, mock_db):
        from database.crud.jobs import count_jobs

        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = [5]
        mock_db.execute.return_value = mock_cursor

        count = await count_jobs(provider="openrouter")
        assert count == 5


class TestDeleteJob:
    @pytest.mark.asyncio
    async def test_delete_job_returns_true(self, mock_db):
        from database.crud.jobs import delete_job

        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_db.execute.return_value = mock_cursor

        result = await delete_job(1)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_job_returns_false_when_missing(self, mock_db):
        from database.crud.jobs import delete_job

        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 0
        mock_db.execute.return_value = mock_cursor

        result = await delete_job(999)
        assert result is False
