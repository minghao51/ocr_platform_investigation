import asyncio
import io
from pathlib import Path
import types

import pytest
from PIL import Image

from auth import create_access_token
from database import crud
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


def _create_test_pdf() -> io.BytesIO:
    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n%minimal")
    buffer.seek(0)
    return buffer


def _create_test_audio() -> io.BytesIO:
    buffer = io.BytesIO()
    buffer.write(b"ID3\x04\x00\x00\x00\x00\x00\x00")
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


def test_analyze_pdf_requires_guest_token_for_guest_upload(
    client, temp_guest_env: Path, monkeypatch: pytest.MonkeyPatch
):
    class _FakePage:
        def get_text(self, _mode):
            return "sample text " * 10

    class _FakeDoc:
        def __iter__(self):
            return iter([_FakePage()])

        def close(self):
            return None

    fake_fitz = types.SimpleNamespace(open=lambda _path: _FakeDoc())
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    upload_response = client.post(
        "/api/upload",
        files={"file": ("guest-sample.pdf", _create_test_pdf(), "application/pdf")},
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    file_id = upload_data["file_id"]
    guest_headers = {"X-Guest-Token": upload_data["guest_token"]}

    allowed_response = client.post(
        f"/api/upload/analyze-pdf/{file_id}",
        headers=guest_headers,
    )
    assert allowed_response.status_code == 200
    assert allowed_response.json()["file_id"] == file_id

    forbidden_response = client.post(f"/api/upload/analyze-pdf/{file_id}")
    assert forbidden_response.status_code == 403


def test_analyze_pdf_rejects_non_owner_user(
    client, temp_guest_env: Path, monkeypatch: pytest.MonkeyPatch
):
    class _FakePage:
        def get_text(self, _mode):
            return "sample text " * 10

    class _FakeDoc:
        def __iter__(self):
            return iter([_FakePage()])

        def close(self):
            return None

    fake_fitz = types.SimpleNamespace(open=lambda _path: _FakeDoc())
    monkeypatch.setitem(__import__("sys").modules, "fitz", fake_fitz)

    file_path = temp_guest_env / "user-owned.pdf"
    file_path.write_bytes(b"%PDF-1.4\n%user-owned")
    file_id = "user-owned-pdf-1"
    asyncio.run(
        crud.create_uploaded_file(
            file_id=file_id,
            original_filename="user-owned.pdf",
            file_extension=".pdf",
            file_path=str(file_path),
            file_size=file_path.stat().st_size,
            content_type="application/pdf",
            user_id=1,
            guest_token=None,
        )
    )

    owner_token = create_access_token(user_id=1, username="owner", is_admin=False)
    other_token = create_access_token(user_id=2, username="other", is_admin=False)

    owner_response = client.post(
        f"/api/upload/analyze-pdf/{file_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_response.status_code == 200

    forbidden_response = client.post(
        f"/api/upload/analyze-pdf/{file_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert forbidden_response.status_code == 403


def test_auto_requires_provider_model_when_pdf_routes_to_provider_method(
    client, temp_guest_env: Path, monkeypatch: pytest.MonkeyPatch
):
    class _Analysis:
        recommended_pipeline = "vision"
        type = "invoice"
        complexity_score = 0.9
        confidence = 0.9
        reasoning = "test"

    class _Classifier:
        def analyze_document(self, _path):
            return _Analysis()

    async def _noop_processing(*_args, **_kwargs):
        return None

    monkeypatch.setattr("routers.processing.DocumentClassifier", lambda: _Classifier())
    monkeypatch.setattr("routers.processing.run_processing_job", _noop_processing)
    monkeypatch.setattr("routers.processing.run_text_processing_job", _noop_processing)

    upload_response = client.post(
        "/api/upload",
        files={"file": ("sample.pdf", _create_test_pdf(), "application/pdf")},
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    guest_headers = {"X-Guest-Token": upload_data["guest_token"]}

    missing_provider_response = client.post(
        "/api/process/",
        json={
            "file_id": upload_data["file_id"],
            "schema_definition": {"type": "object", "properties": {}},
            "extraction_method": "auto",
        },
        headers=guest_headers,
    )
    assert missing_provider_response.status_code == 400
    assert "requires a provider and model" in missing_provider_response.json()["detail"]

    success_response = client.post(
        "/api/process/",
        json={
            "file_id": upload_data["file_id"],
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "schema_definition": {"type": "object", "properties": {}},
            "extraction_method": "auto",
        },
        headers=guest_headers,
    )
    assert success_response.status_code == 200
    assert success_response.json()["job_id"] > 0


@pytest.mark.parametrize(
    ("filename", "mime_type", "payload"),
    [
        (
            "sample.png",
            "image/png",
            {"schema_definition": {"type": "object", "properties": {}}},
        ),
        ("sample.mp3", "audio/mpeg", {}),
    ],
)
def test_auto_with_provider_model_supports_image_and_audio_paths(
    client, temp_guest_env: Path, monkeypatch: pytest.MonkeyPatch, filename, mime_type, payload
):
    async def _noop_processing(*_args, **_kwargs):
        return None

    monkeypatch.setattr("routers.processing.run_processing_job", _noop_processing)
    monkeypatch.setattr("routers.processing.run_text_processing_job", _noop_processing)

    file_bytes = _create_test_image() if mime_type.startswith("image/") else _create_test_audio()
    upload_response = client.post(
        "/api/upload",
        files={"file": (filename, file_bytes, mime_type)},
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
            "extraction_method": "auto",
            **payload,
        },
        headers=guest_headers,
    )

    assert process_response.status_code == 200
    assert process_response.json()["job_id"] > 0
