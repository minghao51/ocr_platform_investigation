# OCR Platform - User Guide

Complete guide for using the OCR Platform to extract structured data from documents using Vision Language Models.

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start Workflow](#quick-start-workflow)
3. [Page-by-Page Guide](#page-by-page-guide)
4. [Schema Templates](#schema-templates)
5. [Creating Custom Schemas](#creating-custom-schemas)
6. [Understanding Results](#understanding-results)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## Introduction

The OCR Platform allows you to:
- **Upload documents** (images and PDFs)
- **Select AI models** from multiple providers (Nebius, OpenRouter, Gemini)
- **Define schemas** to extract structured data
- **View results** in real-time with validation
- **Track history** of all processing jobs

### Supported Document Types
- **Images**: JPEG, PNG, GIF, WebP
- **Documents**: PDF (single and multi-page)
- **Maximum Size**: 10MB per file

### Supported VLM Providers
- **Nebius**: Llama 3.2 11B Vision
- **OpenRouter**: Claude 3.5 Sonnet, GPT-4o, Gemini 1.5 Pro
- **Google Gemini**: Gemini 1.5 Pro, Gemini 1.5 Flash

---

## Quick Start Workflow

### Basic Workflow (5 Steps)

1. **Upload Document**
   - Drag and drop or click to browse
   - Supported: JPG, PNG, GIF, WebP, PDF

2. **Select Model**
   - Choose provider (Nebius, OpenRouter, Gemini)
   - Choose specific model

3. **Choose Schema**
   - Pick a built-in template (Invoice, Receipt, ID Card, Generic)
   - Or create custom JSON schema

4. **Process**
   - Click "Process Document" button
   - Monitor real-time status

5. **View Results**
   - See extracted structured data
   - Copy JSON to clipboard
   - View in history

---

## Page-by-Page Guide

### Page 1: Process Document

The main processing interface.

#### Section 1: File Upload

**Location**: Top of Process page

**How to Use**:
1. **Drag and Drop**: Drag file from your computer onto the upload area
2. **Click to Browse**: Click the upload area to open file picker

**Visual Indicators**:
- Empty: Dashed border with "Drop file here or click to browse"
- Loading: Spinner with "Uploading..."
- Success: Green checkmark with filename preview

**Supported Formats**:
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Documents: `.pdf`

**File Size Limit**: 10MB

**Error Messages**:
- "Invalid file type. Please upload JPG, PNG, GIF, WebP, or PDF."
- "File too large. Maximum size is 10MB."

#### Section 2: Model Selection

**Location**: Below file upload

**Options**:

**Nebius Provider**:
- Model: `meta-llama/Meta-Llama-3.2-11B-Vision-Instruct`
- Good for: General OCR, fast processing, cost-effective

**OpenRouter Provider**:
- Models:
  - `anthropic/claude-3.5-sonnet` - Best for complex layouts
  - `openai/gpt-4o-2024-08-06` - Good for general OCR
  - `google/gemini-pro-1.5` - Balanced performance
  - `meta-llama/llama-3.2-11b-vision-instruct` - Fastest

**Gemini Provider**:
- Models:
  - `gemini-1.5-pro` - Best quality, slower
  - `gemini-1.5-flash` - Fast processing, good quality

**💡 Recommendation**: Start with `gemini-1.5-flash` for speed and free tier.

#### Section 3: Schema Editor

**Location**: Below model selection

**Built-in Templates**:

1. **Invoice** 📄
   - Extracts: Invoice number, date, vendor, line items, totals, tax
   - Best for: Business invoices, bills

2. **Receipt** 🧾
   - Extracts: Merchant, date, items, total, payment method
   - Best for: Store receipts, restaurant receipts

3. **ID Card** 🪪
   - Extracts: Document type, name, DOB, document number, address
   - Best for: Driver's licenses, passports, ID cards

4. **Generic Document** 📝
   - Extracts: Title, content, metadata, entities
   - Best for: General documents, articles, reports

**Custom JSON Schema**:
- Click "Custom Schema" button
- Edit JSON in the text editor
- Must be valid JSON Schema format
- See [Creating Custom Schemas](#creating-custom-schemas)

**Schema Editor Features**:
- Syntax highlighting
- Line numbers
- Error detection for invalid JSON
- Save custom schemas to database

#### Section 4: Process Button

**Location**: Bottom of Process page

**How to Use**:
1. Ensure file is uploaded
2. Select provider and model
3. Choose or create schema
4. Click "Process Document" button

**What Happens**:
1. Button shows "Processing..." with spinner
2. Status updates every 2 seconds:
   - **Pending**: Job queued
   - **Processing**: VLM is analyzing document
   - **Success**: Extraction complete
   - **Error**: Processing failed

#### Section 5: Results Display

**Location**: Appears after processing completes

**Components**:

**Status Badge**:
- ✅ Green: Success
- ❌ Red: Error
- ⏳ Yellow: Processing

**Processing Time**:
- Shows duration (e.g., "Processed in 4.2 seconds")

**Extracted Data**:
- Displayed as formatted JSON
- Readable with syntax highlighting
- Copy button to copy to clipboard

**Error Messages** (if failed):
- Shows specific error code
- Detailed error message
- Suggested fixes

**Actions**:
- **Copy JSON**: Copy results to clipboard
- **Process Another**: Reset form to process new document

---

### Page 2: History

View and manage all past processing jobs.

#### Section 1: Filters

**Location**: Top of History page

**Filter Options**:
- **All Jobs**: Show all processing jobs
- **Success Only**: Show only successful extractions
- **Errors Only**: Show only failed jobs
- **By Provider**: Filter by specific provider (Nebius/OpenRouter/Gemini)

#### Section 2: Jobs Table

**Columns**:
1. **Date/Time**: When job was submitted
2. **File Name**: Name of uploaded file
3. **Provider**: Which VLM was used
4. **Model**: Specific model name
5. **Schema**: Schema template used
6. **Status**: Success/Error badge
7. **Actions**: View and Delete buttons

**Sorting**: Automatically sorted by newest first

#### Section 3: Job Details

**View Job**:
- Click "View" button in actions column
- Modal opens with complete job information:
  - Full extracted JSON data
  - Processing metadata (time, file size)
  - Model details
  - Schema definition used
  - Error details (if failed)

**Delete Job**:
- Click "Delete" button
- Confirms deletion
- Removes job from database permanently
- Cannot be undone

**Copy Results**:
- Inside job detail modal
- Click "Copy JSON" button
- Full job data copied to clipboard

---

## Schema Templates

### Template 1: Invoice

**Purpose**: Extract structured data from invoices and bills.

**Fields Extracted**:
```json
{
  "invoice_number": "string",      // Invoice ID
  "invoice_date": "string",        // Date (YYYY-MM-DD)
  "vendor_name": "string",         // Company name
  "vendor_address": "string",      // Company address
  "line_items": [                  // Array of items
    {
      "description": "string",     // Item description
      "quantity": "number",        // Quantity
      "unit_price": "number",      // Price per unit
      "total": "number"            // Line total
    }
  ],
  "subtotal": "number",            // Subtotal before tax
  "tax_amount": "number",          // Tax amount
  "total_amount": "number",        // Grand total
  "currency": "string",            // Currency code (USD, EUR)
  "due_date": "string",            // Payment due date
  "notes": "string"                // Additional notes
}
```

**Best For**:
- Business invoices
- Utility bills
- Service invoices
- Purchase orders

**Example Output**:
```json
{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "vendor_name": "Acme Corp",
  "line_items": [
    {
      "description": "Web Hosting Service",
      "quantity": 1,
      "unit_price": 99.99,
      "total": 99.99
    }
  ],
  "subtotal": 99.99,
  "tax_amount": 8.99,
  "total_amount": 108.98,
  "currency": "USD"
}
```

### Template 2: Receipt

**Purpose**: Extract data from purchase receipts.

**Fields Extracted**:
```json
{
  "merchant_name": "string",       // Store/restaurant name
  "merchant_address": "string",    // Address
  "transaction_date": "string",    // Purchase date
  "transaction_time": "string",    // Purchase time
  "items": [                       // Array of purchased items
    {
      "name": "string",            // Item name
      "quantity": "number",        // Quantity
      "price": "number",           // Price per item
      "total": "number"            // Line total
    }
  ],
  "subtotal": "number",            // Subtotal
  "tax": "number",                 // Tax amount
  "total": "number",               // Grand total
  "payment_method": "string",      // Cash, card, etc.
  "card_last_4": "string",         // Last 4 digits (if card)
  "transaction_id": "string"       // Receipt ID
}
```

**Best For**:
- Retail store receipts
- Restaurant receipts
- Gas station receipts
- Online purchase confirmations

**Example Output**:
```json
{
  "merchant_name": "Starbucks",
  "transaction_date": "2024-01-15",
  "items": [
    {
      "name": "Caffe Latte",
      "quantity": 2,
      "price": 4.50,
      "total": 9.00
    }
  ],
  "total": 10.35,
  "payment_method": "Credit Card",
  "card_last_4": "1234"
}
```

### Template 3: ID Card

**Purpose**: Extract information from identity documents.

**Fields Extracted**:
```json
{
  "document_type": "string",       // Driver's License, Passport, etc.
  "first_name": "string",          // First name
  "last_name": "string",           // Last name
  "full_name": "string",           // Full name
  "date_of_birth": "string",       // DOB (YYYY-MM-DD)
  "document_number": "string",     // ID/Passport number
  "expiration_date": "string",     // Expiry date
  "issuing_country": "string",     // Country of issue
  "issuing_state": "string",       // State (if applicable)
  "address": {
    "street": "string",            // Street address
    "city": "string",              // City
    "state": "string",             // State/Province
    "zip_code": "string",          // Postal code
    "country": "string"            // Country
  },
  "sex": "string",                 // Gender (M/F/X)
  "height": "string",              // Height (if on ID)
  "weight": "string"               // Weight (if on ID)
}
```

**Best For**:
- Driver's licenses
- Passports
- National ID cards
- State IDs

**Example Output**:
```json
{
  "document_type": "Driver's License",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-05-15",
  "document_number": "D12345678",
  "expiration_date": "2025-05-15",
  "issuing_state": "California",
  "address": {
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94102"
  }
}
```

### Template 4: Generic Document

**Purpose**: Extract general text and entities from any document.

**Fields Extracted**:
```json
{
  "title": "string",               // Document title
  "content": "string",             // Main text content
  "summary": "string",             // Brief summary
  "keywords": ["string"],          // Key terms
  "entities": [                    // Named entities
    {
      "text": "string",            // Entity text
      "type": "string",            // PERSON, ORG, DATE, etc.
      "confidence": "number"       // 0-1 confidence score
    }
  ],
  "metadata": {
    "author": "string",            // Document author
    "date": "string",              // Document date
    "language": "string",          // Detected language
    "page_count": "number"         // Number of pages
  }
}
```

**Best For**:
- Articles and blog posts
- Reports and whitepapers
- Legal documents
- Academic papers
- Any unstructured text

**Example Output**:
```json
{
  "title": "Annual Report 2024",
  "content": "The company achieved record growth...",
  "summary": "Strong financial performance in 2024",
  "keywords": ["growth", "revenue", "expansion"],
  "entities": [
    {
      "text": "John Smith",
      "type": "PERSON",
      "confidence": 0.95
    }
  ],
  "metadata": {
    "author": "Finance Department",
    "language": "en",
    "page_count": 3
  }
}
```

---

## Creating Custom Schemas

### JSON Schema Basics

Custom schemas use **JSON Schema** format to define the structure of extracted data.

### Basic Schema Structure

```json
{
  "type": "object",
  "properties": {
    "field_name": {
      "type": "string",
      "description": "Human-readable description"
    }
  },
  "required": ["field_name"]
}
```

### Supported Data Types

1. **String**: Text data
   ```json
   {"type": "string"}
   ```

2. **Number**: Numeric data (integers or floats)
   ```json
   {"type": "number"}
   ```

3. **Boolean**: True/false
   ```json
   {"type": "boolean"}
   ```

4. **Array**: List of items
   ```json
   {
     "type": "array",
     "items": {"type": "string"}
   }
   ```

5. **Object**: Nested structure
   ```json
   {
     "type": "object",
     "properties": {
       "nested_field": {"type": "string"}
     }
   }
   ```

### Example: Business Card Schema

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Full name of person"
    },
    "title": {
      "type": "string",
      "description": "Job title"
    },
    "company": {
      "type": "string",
      "description": "Company name"
    },
    "email": {
      "type": "string",
      "description": "Email address"
    },
    "phone": {
      "type": "string",
      "description": "Phone number"
    },
    "address": {
      "type": "object",
      "properties": {
        "street": {"type": "string"},
        "city": {"type": "string"},
        "state": {"type": "string"},
        "zip": {"type": "string"},
        "country": {"type": "string"}
      }
    },
    "website": {
      "type": "string",
      "description": "Company website"
    }
  },
  "required": ["name", "company"]
}
```

### Example: Menu Schema

```json
{
  "type": "object",
  "properties": {
    "restaurant_name": {
      "type": "string",
      "description": "Name of restaurant"
    },
    "menu_sections": {
      "type": "array",
      "description": "List of menu sections",
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
        "required": ["section_name", "items"]
      }
    }
  },
  "required": ["restaurant_name", "menu_sections"]
}
```

### Schema Best Practices

1. **Use Descriptions**: Add `description` fields to help the VLM understand each field
2. **Mark Required Fields**: Use `required` array for essential data
3. **Use Appropriate Types**: Choose the most specific type for your data
4. **Nest Logically**: Group related fields in objects
5. **Keep It Simple**: Start simple, add complexity as needed
6. **Test Iteratively**: Test with real documents and refine

---

## Understanding Results

### Success Response

```json
{
  "success": true,
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "success",
  "result": {
    "invoice_number": "INV-001",
    "total_amount": 150.00,
    ...
  },
  "processing_time_seconds": 4.2,
  "provider": "nebius",
  "model": "meta-llama/Meta-Llama-3.2-11B-Vision-Instruct"
}
```

### Error Response

```json
{
  "success": false,
  "status": "error",
  "error_code": "SCHEMA_VALIDATION_FAILED",
  "message": "VLM output did not match the required schema",
  "details": {
    "validation_errors": [
      "total_amount: expected number but got string"
    ],
    "raw_vlm_response": "{...}",
    "schema_definition": "{...}"
  }
}
```

### Common Error Codes

- `INVALID_FILE_TYPE`: File format not supported
- `FILE_TOO_LARGE`: File exceeds 10MB
- `INVALID_JSON_SCHEMA`: Schema is not valid JSON
- `VLM_API_ERROR`: Provider API error
- `VLM_INVALID_JSON`: VLM didn't return valid JSON
- `SCHEMA_VALIDATION_FAILED`: VLM output doesn't match schema

---

## Best Practices

### Document Preparation

1. **Use High-Quality Images**
   - Resolution: At least 1024x768 pixels
   - Good lighting, no shadows
   - Clear, readable text

2. **Scan Documents Properly**
   - Straight alignment (not skewed)
   - No glare or reflections
   - All text visible and in focus

3. **PDF Guidelines**
   - Text-based PDFs work best
   - Scanned PDFs converted to images are OK
   - Multi-page PDFs supported (all pages processed)

### Model Selection

**For Speed**:
- Gemini 1.5 Flash (fastest, good quality)
- Llama 3.2 Vision (fast, cost-effective)

**For Accuracy**:
- Claude 3.5 Sonnet (best for complex layouts)
- Gemini 1.5 Pro (excellent accuracy)
- GPT-4o (strong general performance)

**For Cost**:
- Nebius Llama 3.2 (most cost-effective)
- Gemini 1.5 Flash (free tier available)

### Schema Design

1. **Start Simple**: Begin with basic fields, add complexity gradually
2. **Use Templates**: Built-in templates cover common use cases
3. **Test Real Documents**: Validate with actual documents you'll process
4. **Iterate**: Refine schema based on VLM performance
5. **Handle Edge Cases**: Make optional fields truly optional

### Processing Tips

1. **Batch Similar Documents**: Process documents of the same type together
2. **Monitor Results**: Check first few results to ensure quality
3. **Use History**: Review past jobs to identify patterns
4. **Adjust Models**: Switch models if quality is inconsistent
5. **Validate Results**: Always verify critical data fields

---

## Examples

### Example 1: Processing an Invoice

**Document**: PDF invoice from a vendor

**Steps**:
1. Navigate to **Process** page
2. Upload invoice PDF
3. Select provider: **Gemini**
4. Select model: **gemini-1.5-flash**
5. Select schema: **Invoice** template
6. Click **Process Document**
7. Wait 5-10 seconds
8. View extracted data:
   ```json
   {
     "invoice_number": "INV-2024-1234",
     "vendor_name": "Acme Supplies Inc.",
     "total_amount": 1250.00,
     "due_date": "2024-02-15"
   }
   ```

### Example 2: Processing a Receipt

**Document**: JPG photo of a restaurant receipt

**Steps**:
1. Navigate to **Process** page
2. Upload receipt image
3. Select provider: **OpenRouter**
4. Select model: **claude-3.5-sonnet**
5. Select schema: **Receipt** template
6. Click **Process Document**
7. Wait 3-8 seconds
8. View extracted data with line items

### Example 3: Custom Business Card Schema

**Document**: PNG image of business card

**Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "email": {"type": "string"},
    "phone": {"type": "string"},
    "company": {"type": "string"}
  },
  "required": ["name", "company"]
}
```

**Steps**:
1. Create custom schema in Schema Editor
2. Upload business card image
3. Select model and process
4. Get structured contact information

### Example 4: Multi-Page PDF

**Document**: 5-page contract

**Steps**:
1. Upload 5-page PDF
2. Select model: **gemini-1.5-pro**
3. Select schema: **Generic Document** template
4. Process
5. Results include array of data, one per page

---

## Advanced Features

### Multi-Page PDF Handling

When processing multi-page PDFs:
- Each page is processed separately
- Results are aggregated into an array
- Schema is applied to each page independently
- Processing time scales with page count

**Example Output**:
```json
{
  "success": true,
  "page_count": 3,
  "results": [
    {"page": 1, "title": "Page 1 Content", ...},
    {"page": 2, "title": "Page 2 Content", ...},
    {"page": 3, "title": "Page 3 Content", ...}
  ]
}
```

### Exporting Results

**From Results Display**:
1. Click "Copy JSON" button
2. Paste into text editor or save as `.json` file

**From History**:
1. Click "View" on a job
2. Click "Copy JSON" in modal
3. Paste or save as needed

**Export Formats**:
- JSON (default, full data)
- Can be converted to CSV using external tools
- Can be imported into databases or analytics tools

---

## FAQ

**Q: What's the maximum file size?**
A: 10MB per file. For larger files, split them or contact admin.

**Q: Can I process multiple files at once?**
A: Not currently. Process files one at a time.

**Q: Which model should I use?**
A: Start with `gemini-1.5-flash` for speed and free tier. Upgrade to `claude-3.5-sonnet` for complex layouts.

**Q: How accurate is the extraction?**
A: Accuracy varies by document quality and model. Generally 90-98% for clear documents.

**Q: Can I edit the results after processing?**
A: Not in the UI, but you can copy JSON, edit, and re-import if needed.

**Q: What happens to my data?**
A: All data is stored locally in SQLite database. Documents are sent to VLM providers for processing.

**Q: Is my data private?**
A: Documents are sent to VLM provider APIs. Check their privacy policies. Local storage is not encrypted.

**Q: Can I use this offline?**
A: No, VLM providers require internet connection. Local-only operation is not supported.

**Q: How long does processing take?**
A: Typically 3-15 seconds for single-page documents. Multi-page PDFs take longer.

---

## Getting Help

- **Setup Issues**: See `docs/SETUP_GUIDE.md`
- **Schema Help**: See `SCHEMA_GUIDE.md`
- **API Documentation**: http://localhost:8000/docs
- **Troubleshooting**: See `README.md` troubleshooting section

---

**Last Updated**: 2026-01-16
**Version**: 1.0.0
