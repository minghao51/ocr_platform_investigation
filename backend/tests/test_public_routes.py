"""
Tests for public routes that don't require authentication.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


class TestPublicRoutes:
    """Test public routes return HTML responses."""

    @pytest.fixture
    def client(self):
        """Provide test client for public route tests."""
        return TestClient(app)

    def test_public_routes_return_html(self, client):
        """Test that all public routes return HTML with expected content."""
        public_routes = ["/", "/extract", "/history", "/methodology", "/benchmarks"]

        for route in public_routes:
            response = client.get(route)
            assert response.status_code == 200, f"Route {route} returned {response.status_code}"
            assert "text/html" in response.headers.get("content-type", ""), f"Route {route} not HTML"
            assert "OCR Platform" in response.text, f"Route {route} missing expected content"
