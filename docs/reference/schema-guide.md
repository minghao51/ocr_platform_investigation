# Schema Guide

The extraction layer expects JSON Schema-style definitions.

## Supported Usage Patterns

You can provide schemas in three ways:

1. Built-in templates from `/api/schemas/templates`
2. Saved schemas in the database through `/api/schemas/`
3. Inline `schema_definition` in `/api/process/`

## Built-In Templates

The backend currently exposes:

- `Invoice`
- `Receipt`
- `ID`
- `Generic`

Source: [backend/services/schema_service.py](/Users/minghao/Desktop/personal/ocr_platform_testdrive/backend/services/schema_service.py)

## Minimal Example

```json
{
  "type": "object",
  "properties": {
    "invoice_number": { "type": "string" },
    "total": { "type": "number" }
  },
  "required": ["invoice_number", "total"]
}
```

## Good Practices

- Start with a small object and expand once extraction is reliable.
- Keep field names stable and machine-friendly.
- Mark only genuinely required fields as required.
- Prefer simple object/array structures over deeply nested shapes until needed.
- Use `string` first unless numeric/date parsing is consistently reliable for your documents.

## Common Failure Modes

### Too Strict

If extraction fails validation often, your schema may require fields the document does not always contain.

### Too Broad

If the output is inconsistent, your schema may be too open-ended to guide the model.

### Wrong Data Types

Numeric totals, dates, and optional arrays are the most common type mismatch sources.

## Example Saved Schema Payload

```json
{
  "name": "Receipt Totals",
  "description": "Small schema for merchant/date/total",
  "definition": {
    "type": "object",
    "properties": {
      "merchant": { "type": "string" },
      "date": { "type": "string" },
      "total": { "type": "number" }
    },
    "required": ["merchant", "total"]
  }
}
```
