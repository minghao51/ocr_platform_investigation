import asyncio

from database import crud


def test_create_job_correction_and_fetch(client, auth_header, temp_db_env):
    job_id = asyncio.run(
        crud.create_job(
            file_name="test.pdf",
            file_type="pdf",
            provider="gemini",
            model="gemini-2.5-flash",
            schema_id=None,
            schema_name="Custom",
            processing_method="hybrid",
            user_id=1,
        )
    )
    asyncio.run(
        crud.update_job_status(
            job_id,
            "success",
            result={"invoice_number": "INV-1", "total": 12.5},
            processing_time=1.2,
        )
    )

    response = client.post(
        f"/api/jobs/{job_id}/corrections",
        json={
            "corrected_result": {"invoice_number": "INV-2", "total": 12.5},
            "feedback_tags": ["wrong_field"],
            "notes": "Invoice number was misread",
        },
        headers=auth_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == job_id
    assert payload["feedback_tags"] == ["wrong_field"]
    assert payload["diff_summary"][0]["path"] == "invoice_number"

    history = client.get(f"/api/jobs/{job_id}/corrections", headers=auth_header)
    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_usage_analytics_returns_overview(client, auth_header, temp_db_env):
    response = client.get("/api/analytics/usage", headers=auth_header)

    assert response.status_code == 200
    payload = response.json()
    assert "overview" in payload
    assert "provider_breakdown" in payload
    assert "pipeline_distribution" in payload


def test_schema_suggestion_route_returns_draft(
    client, auth_header, monkeypatch, tmp_path, temp_db_env
):
    uploaded_path = tmp_path / "sample.pdf"
    uploaded_path.write_bytes(b"%PDF-1.4 test")
    file_id = f"schema-suggest-{uploaded_path.stat().st_mtime_ns}"

    asyncio.run(
        crud.create_uploaded_file(
            file_id=file_id,
            original_filename="sample.pdf",
            file_extension=".pdf",
            file_path=str(uploaded_path),
            file_size=uploaded_path.stat().st_size,
            content_type="application/pdf",
            user_id=1,
        )
    )

    async def fake_suggest_schema(self, file_records, provider_name, model, api_key):
        return {
            "provider": provider_name or "gemini",
            "model": model or "gemini-2.5-flash",
            "document_type": "invoice",
            "draft_name": "Invoice Draft",
            "confidence": 0.91,
            "rationale": "Detected recurring invoice fields.",
            "field_descriptions": {"invoice_number": "Invoice identifier"},
            "schema_definition": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": "string"},
                    "total": {"type": "number"},
                },
                "required": ["invoice_number"],
            },
        }

    monkeypatch.setattr(
        "routers.schemas.SchemaSuggestionService.suggest_schema",
        fake_suggest_schema,
    )

    response = client.post(
        "/api/schemas/suggestions",
        json={"file_ids": [file_id]},
        headers=auth_header,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["draft_name"] == "Invoice Draft"
    assert (
        payload["schema_definition"]["properties"]["invoice_number"]["type"] == "string"
    )
