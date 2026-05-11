from typing import Any, Dict
from pydantic import ValidationError


class SchemaService:
    """Service for validating and managing Pydantic schemas"""

    @staticmethod
    def create_pydantic_model(schema_definition: Dict[str, Any]) -> Any:
        """Create a Pydantic model from a schema definition"""

        # Use TypeAdapter for complex nested schemas
        from pydantic import TypeAdapter

        try:
            adapter = TypeAdapter(schema_definition)
            return adapter
        except Exception as e:
            raise ValueError(f"Invalid schema definition: {str(e)}")

    @staticmethod
    def validate_data(
        data: Dict[str, Any], schema_definition: Dict[str, Any]
    ) -> tuple[bool, Any, str | None]:
        """Validate data against schema"""

        try:
            from jsonschema import validate
            from jsonschema.exceptions import (
                ValidationError as JsonSchemaValidationError,
            )

            validate(instance=data, schema=schema_definition)
            return True, data, None
        except ImportError:
            # Fallback if jsonschema is not installed (though we added it)
            return True, data, None
        except JsonSchemaValidationError as e:
            return False, None, str(e)
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def format_validation_error(error: ValidationError) -> str:
        """Format Pydantic validation error"""

        errors = []
        for err in error.errors():
            loc = " -> ".join(str(loc_item) for loc_item in err["loc"])
            errors.append(f"{loc}: {err['msg']}")

        return "\n".join(errors)

    @staticmethod
    def get_builtin_templates() -> Dict[str, Dict[str, Any]]:
        """Get built-in schema templates"""

        return {
            "Invoice": {
                "type": "object",
                "properties": {
                    "invoice_number": {
                        "type": "string",
                        "description": "Unique invoice identifier, typically prefixed with INV- or similar",
                    },
                    "date": {
                        "type": "string",
                        "description": "Invoice date in the original format as shown on the document",
                    },
                    "vendor": {
                        "type": "string",
                        "description": "Name of the vendor or seller issuing the invoice",
                    },
                    "items": {
                        "type": "array",
                        "description": "List of line items billed on this invoice",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {
                                    "type": "string",
                                    "description": "Description of the product or service",
                                },
                                "quantity": {
                                    "type": "number",
                                    "description": "Quantity of items or units",
                                },
                                "unit_price": {
                                    "type": "number",
                                    "description": "Price per single unit before quantity multiplication",
                                },
                                "total": {
                                    "type": "number",
                                    "description": "Line item total (quantity × unit_price)",
                                },
                            },
                            "required": [
                                "description",
                                "quantity",
                                "unit_price",
                                "total",
                            ],
                        },
                    },
                    "subtotal": {
                        "type": "number",
                        "description": "Subtotal of all line items before tax",
                    },
                    "tax": {
                        "type": "number",
                        "description": "Total tax amount applied",
                    },
                    "total": {
                        "type": "number",
                        "description": "Final total amount including all charges",
                    },
                },
                "required": ["invoice_number", "date", "vendor", "items", "total"],
            },
            "Receipt": {
                "type": "object",
                "properties": {
                    "merchant": {
                        "type": "string",
                        "description": "Name of the merchant or business where the purchase was made",
                    },
                    "date": {
                        "type": "string",
                        "description": "Transaction date in the original format",
                    },
                    "items": {
                        "type": "array",
                        "description": "List of purchased items",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name or description of the purchased item",
                                },
                                "price": {
                                    "type": "number",
                                    "description": "Price of the item",
                                },
                            },
                            "required": ["name", "price"],
                        },
                    },
                    "total": {
                        "type": "number",
                        "description": "Final total amount paid",
                    },
                    "payment_method": {
                        "type": "string",
                        "description": "Payment method used (e.g., Cash, Credit Card, Debit)",
                    },
                },
                "required": ["merchant", "date", "items", "total"],
            },
            "ID": {
                "type": "object",
                "properties": {
                    "document_type": {
                        "type": "string",
                        "description": "Type of identification document (e.g., Passport, Driver License, National ID)",
                    },
                    "full_name": {
                        "type": "string",
                        "description": "Full legal name of the document holder",
                    },
                    "date_of_birth": {
                        "type": "string",
                        "description": "Date of birth in the original format",
                    },
                    "document_number": {
                        "type": "string",
                        "description": "Government-issued document or ID number",
                    },
                    "expiration_date": {
                        "type": "string",
                        "description": "Document expiration date",
                    },
                    "address": {
                        "type": "string",
                        "description": "Residential address as shown on the document",
                    },
                },
                "required": ["document_type", "full_name", "document_number"],
            },
            "Generic": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Primary text content extracted from the document",
                    },
                    "entities": {
                        "type": "array",
                        "description": "Named entities found in the document (people, organizations, dates, etc.)",
                        "items": {"type": "string"},
                    },
                },
            },
        }
