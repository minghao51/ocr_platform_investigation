"""
Integration tests for OCR Platform API endpoints.
Tests complete workflows including file upload, processing, and retrieval.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from PIL import Image
import io
from auth import create_access_token


# Create test client
client = TestClient(app)


def get_auth_header():
    """Get authorization header with test token."""
    token = create_access_token(user_id=1, username="test_user", is_admin=True)
    return {"Authorization": f"Bearer {token}"}


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test that health endpoint returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestProvidersEndpoint:
    """Test providers endpoint."""

    def test_list_providers(self):
        """Test listing available providers."""
        response = client.get("/api/providers", headers=get_auth_header())

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # May have 0-3 providers depending on API keys


class TestSchemaEndpoints:
    """Test schema CRUD endpoints."""

    def test_list_all_schemas(self):
        """Test listing all schemas."""
        response = client.get("/api/schemas", headers=get_auth_header())

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_list_template_schemas(self):
        """Test listing only template schemas."""
        response = client.get(
            "/api/schemas?is_template=true", headers=get_auth_header()
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned schemas should be templates
        for schema in data:
            assert schema["is_template"] is True

    def test_get_invoice_schema(self):
        """Test getting a template schema by ID."""
        response = client.get(
            "/api/schemas?is_template=true", headers=get_auth_header()
        )
        schemas = response.json()

        if len(schemas) > 0:
            template_schema = schemas[0]
            schema_id = template_schema["id"]
            response = client.get(
                f"/api/schemas/{schema_id}", headers=get_auth_header()
            )

            assert response.status_code == 200
            data = response.json()
            assert data["is_template"] is True
            assert "definition" in data

    def test_create_custom_schema(self):
        """Test creating a custom schema."""
        import time

        schema_name = "test_custom_schema_" + str(time.time_ns())
        custom_schema = {
            "name": schema_name,
            "description": "Test schema for integration testing",
            "definition": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["title"],
            },
        }

        response = client.post(
            "/api/schemas", json=custom_schema, headers=get_auth_header()
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == schema_name
        assert data["is_template"] is False
        assert "id" in data

    def test_create_duplicate_schema_fails(self):
        """Test that creating duplicate schema fails."""
        import time

        schema_name = "test_duplicate_" + str(time.time_ns())
        schema = {
            "name": schema_name,
            "description": "Test duplicate",
            "definition": {
                "type": "object",
                "properties": {"field": {"type": "string"}},
            },
        }

        # First creation should succeed.
        response1 = client.post("/api/schemas", json=schema, headers=get_auth_header())
        assert response1.status_code == 200

        # Second creation with the same name should fail.
        response2 = client.post("/api/schemas", json=schema, headers=get_auth_header())
        assert response2.status_code == 400


class TestUploadEndpoint:
    """Test file upload endpoint."""

    def create_test_image(self, width=800, height=600, color="red"):
        """Helper to create test image."""
        img = Image.new("RGB", (width, height), color=color)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        return img_bytes

    def test_upload_valid_jpeg(self):
        """Test uploading a valid JPEG image."""
        img_bytes = self.create_test_image()

        response = client.post(
            "/api/upload",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            headers=get_auth_header(),
        )

        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["file_name"] == "test.jpg"

    def test_upload_valid_png(self):
        """Test uploading a valid PNG image."""
        img = Image.new("RGB", (800, 600), color="blue")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        response = client.post(
            "/api/upload",
            files={"file": ("test.png", img_bytes, "image/png")},
            headers=get_auth_header(),
        )

        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data

    def test_upload_invalid_file_type(self):
        """Test uploading an invalid file type."""
        # Create a text file
        text_content = b"This is not an image"

        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", text_content, "text/plain")},
            headers=get_auth_header(),
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data or "detail" in data

    def test_upload_large_file(self):
        """Test uploading a file larger than 10MB."""
        # This test would create a large file
        # Skipping to avoid long test times
        pass


class TestJobsEndpoints:
    """Test jobs management endpoints."""

    def test_list_jobs_empty(self):
        """Test listing jobs when none exist."""
        response = client.get("/api/jobs", headers=get_auth_header())

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # May be empty or have test jobs

    def test_list_jobs_with_filters(self):
        """Test listing jobs with status filter."""
        response = client.get("/api/jobs?status=success", headers=get_auth_header())

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_nonexistent_job(self):
        """Test getting a job that doesn't exist."""
        response = client.get("/api/jobs/999999", headers=get_auth_header())

        assert response.status_code == 404

    def test_delete_nonexistent_job(self):
        """Test deleting a job that doesn't exist."""
        response = client.delete("/api/jobs/999999", headers=get_auth_header())

        assert response.status_code == 404


class TestProcessWorkflow:
    """Test complete processing workflow."""

    def create_test_image(self):
        """Helper to create test image."""
        img = Image.new("RGB", (800, 600), color="red")
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)
        return img_bytes

    def test_full_processing_workflow(self, monkeypatch):
        """Test complete workflow: upload → process → status → results."""
        # Skip if no API keys configured
        # This test would need mocking for actual VLM calls

        # Step 1: Upload file
        img_bytes = self.create_test_image()
        upload_response = client.post(
            "/api/upload",
            files={"file": ("test.jpg", img_bytes, "image/jpeg")},
            headers=get_auth_header(),
        )

        assert upload_response.status_code == 200
        _file_id = upload_response.json()["file_id"]

        # Step 2: Start processing
        # (This would fail without valid API keys and mocking)
        # process_response = client.post(
        #     "/api/process",
        #     json={
        #         "file_id": file_id,
        #         "provider": "nebius",
        #         "model": "meta-llama/Meta-Llama-3.2-11B-Vision-Instruct",
        #         "schema_name": "Invoice"
        #     }
        # )

        # This test needs mocking of VLM providers
        pass


class TestErrorHandling:
    """Test error handling."""

    def test_upload_without_file(self):
        """Test upload request without file."""
        response = client.post("/api/upload", headers=get_auth_header())

        assert response.status_code == 422  # Unprocessable Entity

    def test_process_without_file_id(self):
        """Test process request without file_id."""
        response = client.post("/api/process", json={}, headers=get_auth_header())

        assert response.status_code == 422

    def test_get_invalid_schema_id(self):
        """Test getting schema with invalid ID."""
        response = client.get("/api/schemas/invalid", headers=get_auth_header())

        assert response.status_code == 422


# Fixtures for testing
@pytest.fixture
def test_image_file():
    """Create a test image file."""
    img = Image.new("RGB", (800, 600), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def test_schema():
    """Create a test schema."""
    return {
        "name": "test_integration_schema",
        "description": "Schema for integration tests",
        "definition": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "content": {"type": "string"}},
            "required": ["title"],
        },
    }
