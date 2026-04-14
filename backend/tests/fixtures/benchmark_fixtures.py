"""
Shared fixtures for benchmark testing.
"""

from typing import Any, Dict
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from benchmarks.datasets import BenchmarkSample


# ============================================================================
# Mock VLM Responses
# ============================================================================


def mock_vlm_response(
    content: str,
    prompt_tokens: int = 500,
    completion_tokens: int = 200,
    error: str | None = None,
) -> Dict[str, Any]:
    """Create a mock VLM API response."""
    response: Dict[str, Any] = {
        "content": content,
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
    }
    if error:
        response["error"] = error
    return response


# ============================================================================
# Benchmark Sample Fixtures
# ============================================================================

# Standard receipt sample
STANDARD_RECEIPT_SAMPLE = BenchmarkSample(
    image_path="/fake/path/receipt_001.png",
    expected={
        "total": 25.50,
        "subtotal": 23.00,
        "tax": 2.50,
        "date": "2024-01-15",
        "items": [
            {"name": "Coffee", "price": 4.50, "quantity": 2},
            {"name": "Sandwich", "price": 8.00, "quantity": 1},
            {"name": "Salad", "price": 6.00, "quantity": 1},
        ],
    },
    schema={
        "type": "object",
        "properties": {
            "total": {"type": "number"},
            "subtotal": {"type": "number"},
            "tax": {"type": "number"},
            "date": {"type": "string"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "price": {"type": "number"},
                        "quantity": {"type": "number"},
                    },
                },
            },
        },
    },
    source="test",
    sample_index=0,
)

# CORD modifier sample (from actual CORD data)
CORD_MODIFIER_SAMPLE = BenchmarkSample(
    image_path="/fake/path/receipt_002.png",
    expected={
        "total": 15.75,
        "items": [
            {"name": "VietMilkCoffee++Hot++M", "price": 4.50, "quantity": 1},
            {"name": "Bagel++CreamCheese", "price": 3.25, "quantity": 2},
        ],
    },
    schema={
        "type": "object",
        "properties": {
            "total": {"type": "number"},
            "items": {"type": "array", "items": {"type": "object"}},
        },
    },
    source="cord",
    sample_index=1,
)

# Edge case: items only (no total)
ITEMS_ONLY_SAMPLE = BenchmarkSample(
    image_path="/fake/path/receipt_003.png",
    expected={
        "items": [
            {"name": "Item 1", "price": 10.00},
            {"name": "Item 2", "price": 20.00},
        ]
    },
    schema={
        "type": "object",
        "properties": {"items": {"type": "array"}},
    },
    source="test",
    sample_index=2,
)

# Edge case: dates in various formats
DATE_FORMATS_SAMPLE = BenchmarkSample(
    image_path="/fake/path/receipt_004.png",
    expected={
        "date": "2024-01-15",
        "purchase_date": "01/15/2024",
        "transaction_date": "Jan 15, 2024",
    },
    schema={
        "type": "object",
        "properties": {
            "date": {"type": "string"},
            "purchase_date": {"type": "string"},
            "transaction_date": {"type": "string"},
        },
    },
    source="test",
    sample_index=3,
)

# Edge case: numeric tolerance
NUMERIC_TOLERANCE_SAMPLE = BenchmarkSample(
    image_path="/fake/path/receipt_005.png",
    expected={
        "total": 100.00,
        "subtotal": 90.00,
        "tax": 10.00,
    },
    schema={
        "type": "object",
        "properties": {
            "total": {"type": "number"},
            "subtotal": {"type": "number"},
            "tax": {"type": "number"},
        },
    },
    source="test",
    sample_index=4,
)


# ============================================================================
# Expected VLM Outputs (for testing scoring)
# ============================================================================

# Perfect match output
PERFECT_OUTPUT = mock_vlm_response(
    content="""{
    "total": 25.50,
    "subtotal": 23.00,
    "tax": 2.50,
    "date": "2024-01-15",
    "items": [
        {"name": "Coffee", "price": 4.50, "quantity": 2},
        {"name": "Sandwich", "price": 8.00, "quantity": 1},
        {"name": "Salad", "price": 6.00, "quantity": 1}
    ]
}"""
)

# CORD modifier output (VLM extracts base name without modifiers)
CORD_MODIFIER_OUTPUT = mock_vlm_response(
    content="""{
    "total": 15.75,
    "items": [
        {"name": "Viet Milk Coffee", "price": 4.50, "quantity": 1},
        {"name": "Bagel", "price": 3.25, "quantity": 2}
    ]
}"""
)

# Within 1% tolerance output
WITHIN_TOLERANCE_OUTPUT = mock_vlm_response(
    content="""{
    "total": 100.50,
    "subtotal": 90.45,
    "tax": 10.05
}"""
)

# Outside tolerance output
OUTSIDE_TOLERANCE_OUTPUT = mock_vlm_response(
    content="""{
    "total": 105.00,
    "subtotal": 95.00,
    "tax": 10.50
}"""
)

# Missing fields output
MISSING_FIELDS_OUTPUT = mock_vlm_response(
    content="""{
    "total": 25.50,
    "items": [
        {"name": "Coffee", "price": 4.50}
    ]
}"""
)

# Extra fields output (should not penalize)
EXTRA_FIELDS_OUTPUT = mock_vlm_response(
    content="""{
    "total": 25.50,
    "subtotal": 23.00,
    "tax": 2.50,
    "date": "2024-01-15",
    "store_name": "Test Store",
    "cashier": "John",
    "items": [
        {"name": "Coffee", "price": 4.50, "quantity": 2},
        {"name": "Sandwich", "price": 8.00, "quantity": 1},
        {"name": "Salad", "price": 6.00, "quantity": 1}
    ]
}"""
)

# Error response
ERROR_RESPONSE = mock_vlm_response(content="", error="Rate limit exceeded")


# ============================================================================
# Helper Functions
# ============================================================================


def get_all_fixture_samples() -> list[BenchmarkSample]:
    """Return all fixture samples for batch testing."""
    return [
        STANDARD_RECEIPT_SAMPLE,
        CORD_MODIFIER_SAMPLE,
        ITEMS_ONLY_SAMPLE,
        DATE_FORMATS_SAMPLE,
        NUMERIC_TOLERANCE_SAMPLE,
    ]


def create_mock_provider(responses: list[Dict[str, Any]]):
    """Create a mock provider that returns predefined responses."""

    class MockProvider:
        def __init__(self, responses_list: list[Dict[str, Any]]):
            self.responses = responses_list
            self.index = 0
            self.api_key = "test_key"
            self._in_context = False

        async def __aenter__(self):
            self._in_context = True
            return self

        async def __aexit__(self, *args):
            self._in_context = False
            pass

        async def process_image(self, image, prompt, schema, model, **kwargs):
            _ = image, prompt, schema, model, kwargs  # Mark as intentionally unused
            if not self._in_context:
                raise RuntimeError("MockProvider must be used as async context manager")
            if self.index >= len(self.responses):
                raise IndexError("Not enough mock responses")

            response = self.responses[self.index]
            self.index += 1

            if "error" in response:
                return {"error": response["error"], "usage": {}}

            return {
                "content": response["content"],
                "usage": response.get(
                    "usage",
                    {
                        "prompt_tokens": 500,
                        "completion_tokens": 200,
                    },
                ),
            }

        def get_default_image_size(self):
            return (1024, 1024)

    return MockProvider(responses)
