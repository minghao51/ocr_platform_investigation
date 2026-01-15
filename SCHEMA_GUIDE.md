# Schema Guide

This guide explains how to create and use JSON schemas for structured data extraction in the OCR Platform.

## What is a JSON Schema?

A JSON Schema defines the structure and validation rules for JSON data. In the OCR Platform, schemas tell Vision Language Models (VLMs) exactly what information to extract from documents and how to format it.

## Basic Structure

A JSON schema has the following structure:

```json
{
  "type": "object",
  "properties": {
    "field_name": {
      "type": "string"
    }
  },
  "required": ["field_name"]
}
```

## Supported Data Types

### String
```json
{
  "type": "string"
}
```

### Number
```json
{
  "type": "number"
}
```

### Boolean
```json
{
  "type": "boolean"
}
```

### Array
```json
{
  "type": "array",
  "items": {
    "type": "string"
  }
}
```

### Object (Nested)
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string"
    },
    "age": {
      "type": "number"
    }
  }
}
```

## Built-in Templates

### 1. Invoice Schema

Extracts invoice information including line items:

```json
{
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
}
```

**Example Output:**
```json
{
  "invoice_number": "INV-2024-001",
  "date": "2024-01-15",
  "vendor": "Acme Corp",
  "items": [
    {
      "description": "Widget A",
      "quantity": 5,
      "unit_price": 10.00,
      "total": 50.00
    }
  ],
  "subtotal": 50.00,
  "tax": 5.00,
  "total": 55.00
}
```

### 2. Receipt Schema

Extracts receipt information:

```json
{
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
}
```

### 3. ID Card Schema

Extracts identification document information:

```json
{
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
}
```

### 4. Generic Schema

Extracts free-form text and entities:

```json
{
  "type": "object",
  "properties": {
    "text": {"type": "string"},
    "entities": {
      "type": "array",
      "items": {"type": "string"}
    }
  }
}
```

## Creating Custom Schemas

### Example 1: Business Card Extraction

```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "title": {"type": "string"},
    "company": {"type": "string"},
    "email": {"type": "string"},
    "phone": {"type": "string"},
    "website": {"type": "string"},
    "address": {"type": "string"}
  },
  "required": ["name", "company"]
}
```

### Example 2: Financial Statement

```json
{
  "type": "object",
  "properties": {
    "statement_type": {"type": "string"},
    "period": {"type": "string"},
    "revenue": {"type": "number"},
    "expenses": {"type": "number"},
    "net_income": {"type": "number"},
    "assets": {
      "type": "object",
      "properties": {
        "current": {"type": "number"},
        "non_current": {"type": "number"}
      }
    }
  },
  "required": ["statement_type", "period"]
}
```

### Example 3: Menu Extraction

```json
{
  "type": "object",
  "properties": {
    "restaurant_name": {"type": "string"},
    "menu_sections": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "section_name": {"type": "string"},
          "items": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": {"type": "string"},
                "description": {"type": "string"},
                "price": {"type": "number"}
              },
              "required": ["name", "price"]
            }
          }
        },
        "required": ["section_name"]
      }
    }
  },
  "required": ["restaurant_name", "menu_sections"]
}
```

## Best Practices

### 1. Use Specific Field Names

Choose clear, descriptive field names:

```json
{
  "properties": {
    "customer_full_name": {"type": "string"},  // Good
    "n": {"type": "string"}                     // Bad - unclear
  }
}
```

### 2. Set Appropriate Types

Use the correct data type for each field:

```json
{
  "properties": {
    "quantity": {"type": "number"},    // For calculations
    "phone": {"type": "string"},       // Preserves formatting
    "is_active": {"type": "boolean"}   // Yes/no values
  }
}
```

### 3. Make Important Fields Required

Only require fields that must always be present:

```json
{
  "required": ["invoice_number", "total"]  // Must be present
  // Optional fields like "discount" not included
}
```

### 4. Use Nested Objects for Related Data

Group related information:

```json
{
  "properties": {
    "customer": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"}
      }
    }
  }
}
```

### 5. Handle Arrays for Lists

Use arrays for repeating items:

```json
{
  "properties": {
    "line_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "product": {"type": "string"},
          "quantity": {"type": "number"},
          "price": {"type": "number"}
        }
      }
    }
  }
}
```

## Validation Results

When a document is processed:

### Success
- VLM extracts data matching the schema
- Data is validated against the schema
- Returns validated, structured JSON

### Validation Failure
- VLM returns invalid JSON
- Data doesn't match schema structure
- Required fields missing
- Error message indicates specific validation issue

## Testing Your Schema

1. Start with a simple schema and test
2. Gradually add complexity
3. Test with multiple document samples
4. Review extraction accuracy
5. Adjust field names and types based on results

## Advanced Features

### Nested Arrays
Arrays within arrays for complex data:

```json
{
  "properties": {
    "sections": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "title": {"type": "string"},
          "paragraphs": {
            "type": "array",
            "items": {"type": "string"}
          }
        }
      }
    }
  }
}
```

### Optional Nested Objects
Objects that may or may not be present:

```json
{
  "properties": {
    "shipping_address": {
      "type": "object",
      "properties": {
        "street": {"type": "string"},
        "city": {"type": "string"},
        "zip": {"type": "string"}
      }
    }
  }
}
```

## Common Issues and Solutions

### Issue: Missing Fields

**Problem**: VLM doesn't extract all required fields

**Solutions:**
- Make less critical fields optional
- Improve prompt specificity
- Try different VLM models

### Issue: Wrong Data Types

**Problem**: Numbers returned as strings

**Solutions:**
- VLM may return formatted numbers
- Post-processing may be needed
- Consider using string type and convert later

### Issue: Nested Structure Issues

**Problem**: VLM flattens nested objects

**Solutions:**
- Use more explicit field names
- Simplify schema structure
- Test with different models

## Getting Help

- Review built-in templates for examples
- Test incrementally with simple schemas
- Check API docs for schema endpoints
- Review job history for validation errors
