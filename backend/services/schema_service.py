from typing import Dict, Any, Type
from pydantic import BaseModel, ValidationError
import json

class SchemaService:
    """Service for validating and managing Pydantic schemas"""

    @staticmethod
    def create_pydantic_model(schema_definition: Dict[str, Any]) -> Type[BaseModel]:
        """Create a Pydantic model from a schema definition"""

        # Use TypeAdapter for complex nested schemas
        from pydantic import TypeAdapter

        try:
            # Create a TypeAdapter from the schema
            adapter = TypeAdapter(schema_definition)
            return adapter
        except Exception as e:
            raise ValueError(f"Invalid schema definition: {str(e)}")

    @staticmethod
    def validate_data(
        data: Dict[str, Any],
        schema_definition: Dict[str, Any]
    ) -> tuple[bool, Any, str]:
        """Validate data against schema"""

        try:
            adapter = SchemaService.create_pydantic_model(schema_definition)
            validated_data = adapter.validate_python(data)
            return True, validated_data, None
        except ValidationError as e:
            error_msg = SchemaService.format_validation_error(e)
            return False, None, error_msg
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def format_validation_error(error: ValidationError) -> str:
        """Format Pydantic validation error"""

        errors = []
        for err in error.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            errors.append(f"{loc}: {err['msg']}")

        return "\n".join(errors)

    @staticmethod
    def get_builtin_templates() -> Dict[str, Dict[str, Any]]:
        """Get built-in schema templates"""

        return {
            "Invoice": {
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
                                "total": {"type": "number"}
                            },
                            "required": ["description", "quantity", "unit_price", "total"]
                        }
                    },
                    "subtotal": {"type": "number"},
                    "tax": {"type": "number"},
                    "total": {"type": "number"}
                },
                "required": ["invoice_number", "date", "vendor", "items", "total"]
            },
            "Receipt": {
                "type": "object",
                "properties": {
                    "merchant": {"type": "string"},
                    "date": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "price": {"type": "number"}
                            },
                            "required": ["name", "price"]
                        }
                    },
                    "total": {"type": "number"},
                    "payment_method": {"type": "string"}
                },
                "required": ["merchant", "date", "items", "total"]
            },
            "ID": {
                "type": "object",
                "properties": {
                    "document_type": {"type": "string"},
                    "full_name": {"type": "string"},
                    "date_of_birth": {"type": "string"},
                    "document_number": {"type": "string"},
                    "expiration_date": {"type": "string"},
                    "address": {"type": "string"}
                },
                "required": ["document_type", "full_name", "document_number"]
            },
            "Generic": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        }
