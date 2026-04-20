import asyncio
import io
from pathlib import Path

import pytest
from PIL import Image

from database.migrations import run_migrations


@pytest.fixture
def temp_guest_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "guest-access.db"
    uploads_dir = tmp_path / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("database.pool.get_db_path", lambda: db_path)
    monkeypatch.setattr("database.migrations._get_db_path", lambda: db_path)
    monkeypatch.setattr("dependencies._get_cached_db_path", lambda: db_path)
    monkeypatch.setattr("routers.upload.UPLOAD_DIR", uploads_dir)

    asyncio.run(run_migrations())
    return uploads_dir


def _create_test_image() -> io.BytesIO:
    image = Image.new("RGB", (64, 64), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _create_test_docx() -> io.BytesIO:
    buffer = io.BytesIO()
    buffer.write(b"PK\x03\x04minimal-docx")
    buffer.seek(0)
    return buffer


def test_guest_can_upload_process_and_read_own_job(
    client, temp_guest_env: Path, monkeypatch: pytest.MonkeyPatch
):
    async def _noop_processing(*_args, **_kwargs):
        return None

    monkeypatch.setattr("routers.processing.run_processing_job", _noop_processing)
    monkeypatch.setattr("routers.processing.run_text_processing_job", _noop_processing)

    upload_response = client.post(
        "/api/upload",
        files={"file": ("guest-sample.png", _create_test_image(), "image/png")},
    )

    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["file_id"]
    assert upload_data["guest_token"]

    guest_headers = {"X-Guest-Token": upload_data["guest_token"]}
    process_response = client.post(
        "/api/process/",
        json={
            "file_id": upload_data["file_id"],
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "schema_definition": {
                "type": "object",
                "properties": {"title": {"type": "string"}},
            },
            "extraction_method": "vision",
        },
        headers=guest_headers,
    )

    assert process_response.status_code == 200
    process_data = process_response.json()
    assert process_data["job_id"]
    assert process_data["guest_token"] == upload_data["guest_token"]

    status_response = client.get(
        f"/api/process/status/{process_data['job_id']}",
        headers=guest_headers,
    )
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["job_id"] == process_data["job_id"]
    assert status_data["status"] in {"pending", "processing", "success"}

    forbidden_response = client.get(f"/api/process/status/{process_data['job_id']}")
    assert forbidden_response.status_code == 403


def test_guest_can_queue_transcription_for_docx(
    client, temp_guest_env: Path, monkeypatch: pytest.MonkeyPatch
):
    async def _noop_processing(*_args, **_kwargs):
        return None

    monkeypatch.setattr("routers.processing.run_processing_job", _noop_processing)

    upload_response = client.post(
        "/api/upload",
        files={
            "file": (
                "guest-sample.docx",
                _create_test_docx(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert upload_response.status_code == 200
    upload_data = upload_response.json()

    guest_headers = {"X-Guest-Token": upload_data["guest_token"]}
    process_response = client.post(
        "/api/process/",
        json={
            "file_id": upload_data["file_id"],
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "extraction_method": "transcription",
        },
        headers=guest_headers,
    )

    assert process_response.status_code == 200
    process_data = process_response.json()
    assert process_data["job_id"]
    assert process_data["guest_token"] == upload_data["guest_token"]


def test_document_rejects_vision_processing(
    client, temp_guest_env: Path, monkeypatch: pytest.MonkeyPatch
):
    async def _noop_processing(*_args, **_kwargs):
        return None

    monkeypatch.setattr("routers.processing.run_processing_job", _noop_processing)

    upload_response = client.post(
        "/api/upload",
        files={
            "file": (
                "guest-sample.docx",
                _create_test_docx(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    guest_headers = {"X-Guest-Token": upload_response.json()["guest_token"]}
    process_response = client.post(
        "/api/process/",
        json={
            "file_id": upload_response.json()["file_id"],
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "schema_definition": {"type": "object", "properties": {}},
            "extraction_method": "vision",
        },
        headers=guest_headers,
    )

    assert process_response.status_code == 400
    assert "docling-parse" in process_response.json()["detail"]
