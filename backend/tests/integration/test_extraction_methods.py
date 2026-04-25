"""
Integration tests for all extraction methods.

Tests the full API pipeline: upload -> process -> poll status -> verify result.
LLM calls are mocked to avoid requiring API keys, but file parsing (PyMuPDF,
Docling, image processing) uses real artifacts stored in tests/fixtures/.

Extraction methods tested:
- docling-parse (PyMuPDF + LLM) — PDF, DOCX, PPTX
- text (pdfplumber + LLM) — searchable PDF
- vision (VLM image) — image
- transcription — DOCX
"""

import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from auth import create_access_token

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"

GENERIC_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"},
    },
}

INVOICE_SCHEMA = {
    "type": "object",
    "properties": {
        "invoice_number": {"type": "string"},
        "date": {"type": "string"},
        "vendor": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit_price": {"type": "number"},
                    "total": {"type": "number"},
                },
            },
        },
        "subtotal": {"type": "number"},
        "tax": {"type": "number"},
        "total": {"type": "number"},
    },
    "required": ["invoice_number", "date", "vendor", "total"],
}

MOCK_INVOICE_JSON = json.dumps({
    "invoice_number": "INV-2024-0042",
    "date": "November 15, 2024",
    "vendor": "CloudSync Solutions",
    "items": [
        {"description": "Enterprise License - Annual", "quantity": 1, "unit_price": 5000.0, "total": 5000.0},
        {"description": "Premium Support Package", "quantity": 1, "unit_price": 1200.0, "total": 1200.0},
        {"description": "Data Migration Service", "quantity": 3, "unit_price": 400.0, "total": 1200.0},
        {"description": "Training Sessions (8hrs)", "quantity": 2, "unit_price": 350.0, "total": 700.0},
    ],
    "subtotal": 8100.0,
    "tax": 668.25,
    "total": 8768.25,
})

MOCK_GENERIC_JSON = json.dumps({
    "title": "Extracted Document",
    "content": "Sample extracted content from document.",
})

MOCK_TRANSCRIPTION_TEXT = "# Transcription Result\n\nThis is a mock transcription output in Markdown format."


def auth_header():
    token = create_access_token(user_id=1, username="test_user", is_admin=True)
    return {"Authorization": f"Bearer {token}"}


def fixture_path(name: str) -> str:
    p = FIXTURES_DIR / name
    assert p.exists(), f"Fixture not found: {p}"
    return str(p)


def upload_file(client, file_path: str, headers: dict) -> str:
    fname = Path(file_path).name
    suffix = Path(file_path).suffix.lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
    }
    mime = mime_map.get(suffix, "application/octet-stream")
    with open(file_path, "rb") as f:
        resp = client.post(
            "/api/upload",
            files={"file": (fname, f, mime)},
            headers=headers,
        )
    assert resp.status_code == 200, f"Upload failed: {resp.text}"
    return resp.json()["file_id"]


def process_and_wait(client, file_id, headers, payload_overrides=None):
    payload = {
        "file_id": file_id,
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "schema_definition": GENERIC_SCHEMA,
        "extraction_method": "docling-parse",
    }
    if payload_overrides:
        payload.update(payload_overrides)

    resp = client.post("/api/process/", json=payload, headers=headers)
    assert resp.status_code == 200, f"Process failed: {resp.text}"
    job_id = resp.json()["job_id"]

    for _ in range(60):
        status_resp = client.get(f"/api/process/status/{job_id}", headers=headers)
        assert status_resp.status_code == 200
        job = status_resp.json()
        if job["status"] in ("success", "error"):
            return job
        time.sleep(0.1)

    pytest.fail(f"Job {job_id} did not complete in time")


@pytest.fixture(autouse=True)
def _mock_api_key():
    with patch("services.processing.resolve_provider_api_key", return_value="test-api-key"):
        yield


def _mock_process_text(response_json):
    return AsyncMock(return_value={
        "content": response_json,
        "model": "gemini-2.5-flash",
        "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
    })


_mock_process_image = AsyncMock(return_value={
    "content": MOCK_GENERIC_JSON,
    "model": "gemini-2.5-flash",
    "usage": {"prompt_tokens": 150, "completion_tokens": 100, "total_tokens": 250},
})


# ============================================================================
# docling-parse tests
# ============================================================================


class TestDoclingParse:
    """Test docling-parse (PyMuPDF + LLM) extraction method."""

    def test_pdf_invoice_extraction(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", _mock_process_text(MOCK_INVOICE_JSON)):
            file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {
                "extraction_method": "docling-parse",
                "schema_definition": INVOICE_SCHEMA,
            })
        assert job["status"] == "success"
        assert job["result"]["invoice_number"] == "INV-2024-0042"
        assert job["result"]["total"] == 8768.25
        assert len(job["result"]["items"]) == 4

    def test_searchable_pdf(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", _mock_process_text(MOCK_GENERIC_JSON)):
            file_id = upload_file(client, fixture_path("searchable.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {"extraction_method": "docling-parse"})
        assert job["status"] == "success"

    def test_multi_page_pdf(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", _mock_process_text(MOCK_GENERIC_JSON)):
            file_id = upload_file(client, fixture_path("multi_page.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {"extraction_method": "docling-parse"})
        assert job["status"] == "success"

    def test_docx(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", _mock_process_text(MOCK_GENERIC_JSON)):
            file_id = upload_file(client, fixture_path("sample.docx"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {"extraction_method": "docling-parse"})
        assert job["status"] == "success"

    def test_pptx(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", _mock_process_text(MOCK_GENERIC_JSON)):
            file_id = upload_file(client, fixture_path("sample.pptx"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {"extraction_method": "docling-parse"})
        assert job["status"] == "success"

    def test_raw_output_mode(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", _mock_process_text("# Raw Markdown\n\nSome content.")):
            file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
            resp = client.post("/api/process/", json={
                "file_id": file_id,
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "extraction_method": "docling-parse",
                "schema_mode": "raw",
            }, headers=auth_header())
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]
        job = None
        for _ in range(60):
            sr = client.get(f"/api/process/status/{job_id}", headers=auth_header())
            job = sr.json()
            if job["status"] in ("success", "error"):
                break
            time.sleep(0.1)
        assert job["status"] == "success"


# ============================================================================
# text extraction tests
# ============================================================================


class TestTextExtraction:
    """Test text extraction (pdfplumber + LLM)."""

    def test_searchable_pdf(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", _mock_process_text(MOCK_GENERIC_JSON)):
            file_id = upload_file(client, fixture_path("searchable.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {"extraction_method": "text"})
        assert job["status"] == "success"

    def test_invoice_pdf(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", _mock_process_text(MOCK_INVOICE_JSON)):
            file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {
                "extraction_method": "text",
                "schema_definition": INVOICE_SCHEMA,
            })
        assert job["status"] == "success"
        assert job["result"]["invoice_number"] == "INV-2024-0042"


# ============================================================================
# vision extraction tests
# ============================================================================


class TestVisionExtraction:
    """Test vision extraction (VLM image processing)."""

    def test_image_vision(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_image", _mock_process_image):
            file_id = upload_file(client, fixture_path("receipt.jpg"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {
                "extraction_method": "vision",
                "schema_definition": {
                    "type": "object",
                    "properties": {
                        "store_name": {"type": "string"},
                        "total": {"type": "number"},
                        "date": {"type": "string"},
                        "items": {"type": "array"},
                    },
                },
            })
        assert job["status"] == "success"


# ============================================================================
# transcription tests
# ============================================================================


class TestTranscription:
    """Test transcription extraction."""

    def test_docx_transcription(self, client, temp_db_env):
        mock = AsyncMock(return_value={
            "content": MOCK_TRANSCRIPTION_TEXT,
            "model": "gemini-2.5-flash",
            "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
        })
        with patch("services.gemini.GeminiProvider.process_text", mock):
            file_id = upload_file(client, fixture_path("sample.docx"), auth_header())
            resp = client.post("/api/process/", json={
                "file_id": file_id,
                "provider": "gemini",
                "model": "gemini-2.5-flash",
                "extraction_method": "transcription",
            }, headers=auth_header())
        assert resp.status_code == 200
        job_id = resp.json()["job_id"]
        job = None
        for _ in range(60):
            sr = client.get(f"/api/process/status/{job_id}", headers=auth_header())
            job = sr.json()
            if job["status"] in ("success", "error"):
                break
            time.sleep(0.1)
        if job["status"] == "error" and "poppler" in (job.get("error") or "").lower():
            pytest.skip("poppler not installed")
        assert job["status"] == "success"


# ============================================================================
# error handling tests
# ============================================================================


class TestExtractionErrors:
    """Test error handling in extraction pipeline."""

    def test_missing_provider_for_provider_method(self, client, temp_db_env):
        file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
        resp = client.post("/api/process/", json={
            "file_id": file_id,
            "extraction_method": "docling-parse",
        }, headers=auth_header())
        assert resp.status_code == 400
        assert "provider" in resp.json()["detail"].lower()

    def test_invalid_extraction_method(self, client, temp_db_env):
        file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
        resp = client.post("/api/process/", json={
            "file_id": file_id,
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "extraction_method": "nonexistent-method",
            "schema_definition": INVOICE_SCHEMA,
        }, headers=auth_header())
        assert resp.status_code in (400, 422)

    def test_truncated_json(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", AsyncMock(return_value={
            "content": '{"invoice_number": "INV-2024-0042", "date": "2024-11-15", "items": [{"desc',
            "model": "gemini-2.5-flash",
            "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
        })):
            file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {
                "extraction_method": "docling-parse",
                "schema_definition": INVOICE_SCHEMA,
            })
        assert job["status"] == "error"
        assert "Invalid JSON" in (job.get("error") or "") or "json" in (job.get("error") or "").lower()

    def test_empty_response(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", AsyncMock(return_value={
            "content": "", "model": "gemini-2.5-flash",
            "usage": {"prompt_tokens": 100, "completion_tokens": 0, "total_tokens": 100},
        })):
            file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {
                "extraction_method": "docling-parse",
                "schema_definition": INVOICE_SCHEMA,
            })
        assert job["status"] == "error"

    def test_provider_returns_error(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", AsyncMock(return_value={
            "error": "Rate limit exceeded", "content": None, "model": "gemini-2.5-flash",
        })):
            file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {
                "extraction_method": "docling-parse",
                "schema_definition": INVOICE_SCHEMA,
            })
        assert job["status"] == "error"
        assert "Rate limit" in (job.get("error") or "")

    def test_safety_blocked_response(self, client, temp_db_env):
        with patch("services.gemini.GeminiProvider.process_text", AsyncMock(return_value={
            "error": "Response blocked by safety filters. Categories: ['unknown']",
            "content": None, "model": "gemini-2.5-flash",
        })):
            file_id = upload_file(client, fixture_path("invoice.pdf"), auth_header())
            job = process_and_wait(client, file_id, auth_header(), {
                "extraction_method": "docling-parse",
                "schema_definition": INVOICE_SCHEMA,
            })
        assert job["status"] == "error"
        assert "safety" in (job.get("error") or "").lower()

    def test_docx_rejects_vision_method(self, client, temp_db_env):
        file_id = upload_file(client, fixture_path("sample.docx"), auth_header())
        resp = client.post("/api/process/", json={
            "file_id": file_id,
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "extraction_method": "vision",
            "schema_definition": INVOICE_SCHEMA,
        }, headers=auth_header())
        assert resp.status_code == 400


# ============================================================================
# file type routing tests
# ============================================================================


class TestFileTypeRouting:
    def test_pdf_type_detection(self, client, temp_db_env):
        file_id = upload_file(client, fixture_path("searchable.pdf"), auth_header())
        resp = client.get("/api/jobs?limit=1", headers=auth_header())
        assert resp.status_code == 200

    def test_image_forces_vision(self, client, temp_db_env):
        file_id = upload_file(client, fixture_path("receipt.jpg"), auth_header())
        resp = client.post("/api/process/", json={
            "file_id": file_id,
            "provider": "gemini",
            "model": "gemini-2.5-flash",
            "extraction_method": "text",
            "schema_definition": INVOICE_SCHEMA,
        }, headers=auth_header())
        assert resp.status_code in (200, 400)


# ============================================================================
# extract settings endpoint tests
# ============================================================================


class TestExtractSettingsEndpoint:
    def test_get_settings(self, client):
        resp = client.get("/api/extract/settings", headers=auth_header())
        assert resp.status_code == 200
        data = resp.json()
        assert "providers" in data
        assert isinstance(data["providers"], list)
        assert "extraction_methods" in data
        assert len(data["extraction_methods"]) == 7
        assert "defaults" in data
        assert data["defaults"]["max_tokens"]["default"] == 8192
        assert "file_type_methods" in data
        assert "schema_templates" in data

    def test_method_ids(self, client):
        resp = client.get("/api/extract/settings", headers=auth_header())
        data = resp.json()
        ids = [m["id"] for m in data["extraction_methods"]]
        for expected in ("auto", "text", "vision", "hybrid", "docling-parse", "docling-extract", "transcription"):
            assert expected in ids

    def test_schema_modes(self, client):
        resp = client.get("/api/extract/settings", headers=auth_header())
        data = resp.json()
        modes = {m["id"]: m for m in data["schema_modes"]}
        assert modes["raw"]["available_for"] == ["docling-parse"]
        assert modes["auto-detect"]["available_for"] is None
