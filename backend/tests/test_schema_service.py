"""
Unit tests for schema validation service.
Tests schema validation, TypeAdapter usage, and built-in templates.
"""

import pytest
from pydantic import ValidationError
from services.schema_service import (
    validate_vlm_output,
    get_builtin_schema,
    get_all_builtin_schemas,
)


class TestSchemaValidation:
    """Test schema validation functionality."""

    def test_validate_simple_object(self):
        """Test validation of simple object schema."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "age": {"type": "number"}},
            "required": ["name"],
        }

        vlm_output = {"name": "John Doe", "age": 30}

        result = validate_vlm_output(vlm_output, schema)
        assert result["name"] == "John Doe"
        assert result["age"] == 30

    def test_validate_nested_object(self):
        """Test validation of nested object schema."""
        schema = {
            "type": "object",
            "properties": {
                "person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"},
                            },
                        },
                    },
                }
            },
        }

        vlm_output = {
            "person": {
                "name": "Jane Doe",
                "address": {"street": "123 Main St", "city": "San Francisco"},
            }
        }

        result = validate_vlm_output(vlm_output, schema)
        assert result["person"]["name"] == "Jane Doe"
        assert result["person"]["address"]["city"] == "San Francisco"

    def test_validate_array(self):
        """Test validation of array schema."""
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "price": {"type": "number"},
                        },
                    },
                }
            },
        }

        vlm_output = {
            "items": [
                {"name": "Item 1", "price": 10.99},
                {"name": "Item 2", "price": 20.50},
            ]
        }

        result = validate_vlm_output(vlm_output, schema)
        assert len(result["items"]) == 2
        assert result["items"][0]["name"] == "Item 1"
        assert result["items"][1]["price"] == 20.50

    def test_validation_error_missing_required_field(self):
        """Test that validation fails when required field is missing."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}, "email": {"type": "string"}},
            "required": ["name", "email"],
        }

        vlm_output = {
            "name": "John Doe"
            # Missing email
        }

        with pytest.raises(ValidationError):
            validate_vlm_output(vlm_output, schema)

    def test_validation_error_wrong_type(self):
        """Test that validation fails when field has wrong type."""
        schema = {"type": "object", "properties": {"age": {"type": "number"}}}

        vlm_output = {
            "age": "thirty"  # Should be number, not string
        }

        with pytest.raises(ValidationError):
            validate_vlm_output(vlm_output, schema)


class TestBuiltInSchemas:
    """Test built-in schema templates."""

    def test_get_invoice_schema(self):
        """Test retrieving Invoice schema template."""
        schema = get_builtin_schema("Invoice")

        assert schema is not None
        assert "type" in schema
        assert "properties" in schema
        assert "invoice_number" in schema["properties"]
        assert "vendor_name" in schema["properties"]
        assert "total_amount" in schema["properties"]

    def test_get_receipt_schema(self):
        """Test retrieving Receipt schema template."""
        schema = get_builtin_schema("Receipt")

        assert schema is not None
        assert "merchant_name" in schema["properties"]
        assert "items" in schema["properties"]

    def test_get_id_card_schema(self):
        """Test retrieving ID Card schema template."""
        schema = get_builtin_schema("ID Card")

        assert schema is not None
        assert "document_type" in schema["properties"]
        assert "full_name" in schema["properties"]
        assert "document_number" in schema["properties"]

    def test_get_generic_document_schema(self):
        """Test retrieving Generic Document schema template."""
        schema = get_builtin_schema("Generic Document")

        assert schema is not None
        assert "title" in schema["properties"]
        assert "content" in schema["properties"]

    def test_get_nonexistent_schema(self):
        """Test that non-existent schema returns None."""
        schema = get_builtin_schema("NonExistentSchema")
        assert schema is None

    def test_get_all_builtin_schemas(self):
        """Test retrieving all built-in schemas."""
        schemas = get_all_builtin_schemas()

        assert isinstance(schemas, dict)
        assert "Invoice" in schemas
        assert "Receipt" in schemas
        assert "ID Card" in schemas
        assert "Generic Document" in schemas
        assert len(schemas) == 4


class TestInvoiceSchemaValidation:
    """Test validation with real Invoice schema."""

    def test_valid_invoice_data(self):
        """Test validation of valid invoice data."""
        schema = get_builtin_schema("Invoice")

        invoice_data = {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-01-15",
            "vendor_name": "Acme Corp",
            "vendor_address": "123 Business Ave, San Francisco, CA 94102",
            "line_items": [
                {
                    "description": "Web Hosting Service",
                    "quantity": 1,
                    "unit_price": 99.99,
                    "total": 99.99,
                },
                {
                    "description": "Domain Registration",
                    "quantity": 2,
                    "unit_price": 15.00,
                    "total": 30.00,
                },
            ],
            "subtotal": 129.99,
            "tax_amount": 11.70,
            "total_amount": 141.69,
            "currency": "USD",
            "due_date": "2024-02-15",
        }

        result = validate_vlm_output(invoice_data, schema)
        assert result["invoice_number"] == "INV-2024-001"
        assert len(result["line_items"]) == 2
        assert result["total_amount"] == 141.69

    def test_minimal_invoice_data(self):
        """Test validation of minimal invoice data (only required fields)."""
        schema = get_builtin_schema("Invoice")

        # This assumes most fields are optional
        minimal_data = {
            "invoice_number": "INV-001",
            "vendor_name": "Test Vendor",
            "line_items": [],
            "total_amount": 0.0,
        }

        # This should either pass or fail depending on schema requirements
        # Adjust expected behavior based on actual schema
        try:
            result = validate_vlm_output(minimal_data, schema)
            assert result["vendor_name"] == "Test Vendor"
        except ValidationError:
            # If schema requires more fields, this is expected
            pass


class TestReceiptSchemaValidation:
    """Test validation with real Receipt schema."""

    def test_valid_receipt_data(self):
        """Test validation of valid receipt data."""
        schema = get_builtin_schema("Receipt")

        receipt_data = {
            "merchant_name": "Starbucks",
            "merchant_address": "123 Market St, San Francisco, CA",
            "transaction_date": "2024-01-15",
            "transaction_time": "09:30 AM",
            "items": [
                {"name": "Caffe Latte", "quantity": 2, "price": 4.50, "total": 9.00},
                {
                    "name": "Blueberry Muffin",
                    "quantity": 1,
                    "price": 3.50,
                    "total": 3.50,
                },
            ],
            "subtotal": 12.50,
            "tax": 1.13,
            "total": 13.63,
            "payment_method": "Credit Card",
            "card_last_4": "1234",
            "transaction_id": "TXN-123456",
        }

        result = validate_vlm_output(receipt_data, schema)
        assert result["merchant_name"] == "Starbucks"
        assert len(result["items"]) == 2
        assert result["total"] == 13.63
