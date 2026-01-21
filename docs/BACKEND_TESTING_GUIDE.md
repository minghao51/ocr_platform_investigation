# Backend Testing Guide

Quick reference guide for testing the OCR Platform backend.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Running Unit Tests](#running-unit-tests)
3. [Running Integration Tests](#running-integration-tests)
4. [Test Scripts](#test-scripts)
5. [Testing Workflows](#testing-workflows)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# Install test dependencies
cd backend
pip install -r requirements-test.txt

# Ensure backend server is running (for integration tests)
uvicorn main:app --reload --port 8000
```

### Run All Tests

```bash
# From backend directory
pytest tests/ -v

# With coverage report
pytest tests/ --cov=services --cov-report=html
```

---

## Running Unit Tests

### Schema Service Tests

Tests schema validation, built-in templates, and JSON parsing.

```bash
# Run all schema tests
pytest tests/test_schema_service.py -v

# Run specific test
pytest tests/test_schema_service.py::TestSchemaValidation::test_validate_simple_object -v
```

**Test Coverage:**
- Simple, nested, and array validation
- Required field validation
- Type validation
- Built-in schemas (Invoice, Receipt, ID Card, Generic Document)
- Error handling

### Image Service Tests

Tests image resizing, base64 encoding, and provider-specific constraints.

```bash
# Run all image tests
pytest tests/test_image_service.py -v

# Run specific test
pytest tests/test_image_service.py::test_resize_large_image_nebius -v
```

**Test Coverage:**
- Image resizing for Nebius, Gemini, OpenRouter
- Aspect ratio preservation
- Base64 encoding (JPEG, PNG)
- Provider-specific constraints
- PDF to image conversion

### Result Parsing Tests

Tests job status parsing and JSON result handling.

```bash
# Run result parsing test
pytest tests/test_fix_result_parsing.py -v
```

**Test Coverage:**
- JSON string → dict conversion
- Job status response structure
- Error message handling

---

## Running Integration Tests

### All Integration Tests

Tests complete API workflows from upload to processing.

```bash
# Run all integration tests
pytest tests/test_integration.py -v
```

**Note:** Some tests require the backend server to be running.

### Test Categories

**Health Check:**
```bash
pytest tests/test_integration.py::TestHealthEndpoint -v
```

**Providers:**
```bash
pytest tests/test_integration.py::TestProvidersEndpoint -v
```

**Schema CRUD:**
```bash
pytest tests/test_integration.py::TestSchemaEndpoints -v
```

**File Upload:**
```bash
pytest tests/test_integration.py::TestUploadEndpoint -v
```

**Jobs Management:**
```bash
pytest tests/test_integration.py::TestJobsEndpoints -v
```

---

## Test Scripts

Three standalone scripts are provided for common testing tasks in `backend/scripts/`.

### 1. Simple Upload Test

Tests file upload endpoint with local documents.

```bash
# Basic usage
python scripts/test_upload.py path/to/document.pdf

# With custom backend URL
python scripts/test_upload.py image.jpg --url http://localhost:8000

# Display full API response
python scripts/test_upload.py document.png --verbose
```

**Features:**
- ✅ Validates file size (max 10MB)
- ✅ Validates file type (JPG, PNG, PDF)
- ✅ Displays file_id and metadata
- ✅ Clear error messages

**Example Output:**
```
📤 Uploading file...
   File: invoice.pdf
   Size: 245.67 KB
   Type: .pdf
   URL: http://localhost:8000/api/upload/

✅ Upload successful!

📋 File Metadata:
   File ID:      abc123-def456-ghi789
   File Name:    invoice.pdf
   File Type:    pdf
   File Size:    251528 bytes
   File Path:    data/uploads/abc123-def456-ghi789.pdf

💡 Use this file_id for processing:
   --file-id abc123-def456-ghi789
```

---

### 2. Schema Parsing Test

Upload a document and parse it with a specific schema.

```bash
# Parse with Invoice schema (uses default provider)
python scripts/test_schema_parsing.py invoice.pdf --schema Invoice

# Parse with specific provider
python scripts/test_schema_parsing.py receipt.jpg --schema Receipt --provider nebius

# Parse with specific model
python scripts/test_schema_parsing.py id.png --schema "ID Card" --provider gemini --model gemini-2.5-flash

# List available providers and models
python scripts/test_schema_parsing.py --list-providers
```

**Supported Schemas:**
- `Invoice` - Invoice documents with line items
- `Receipt` - Receipt/transaction documents
- `ID Card` - ID cards and passports
- `Generic Document` - Generic text extraction

**Features:**
- ✅ Automatic provider selection if not specified
- ✅ Real-time status polling
- ✅ Processing time tracking
- ✅ Pretty-printed extracted data
- ✅ Error handling with tips

**Example Output:**
```
🔍 Schema Parsing Test
==================================================
   File:     invoice.pdf
   Schema:   Invoice
   API URL:  http://localhost:8000

✅ Schema found: Invoice
   Provider: gemini
   Model:    gemini-2.5-flash

📤 Step 1: Uploading file...
✅ File uploaded: abc123-def456

⚙️  Step 2: Starting processing...
✅ Job started: 42

⏳ Step 3: Waiting for results...
   Status:  SUCCESS ✓

📊 Step 4: Results
==================================================
⏱️  Processing Time: 23.45 seconds

✅ Processing successful!

📊 Extracted Data:
{
  "invoice_number": "INV-2024-001",
  "vendor_name": "Acme Corp",
  "line_items": [...],
  "total_amount": 141.69
}
```

---

### 3. Batch Testing Script

Test multiple documents at once for regression testing.

```bash
# Test all documents in a directory
python scripts/batch_test_parsing.py ./test_documents/ --schema Invoice

# Test with specific provider
python scripts/batch_test_parsing.py ./receipts/ --schema Receipt --provider nebius

# Parallel processing (faster for multiple documents)
python scripts/batch_test_parsing.py ./docs/ --schema "Generic Document" --parallel 3

# Save results to JSON file
python scripts/batch_test_parsing.py ./invoices/ --schema Invoice --output results.json

# Custom timeout for large PDFs
python scripts/batch_test_parsing.py ./large_pdfs/ --schema Invoice --timeout 180
```

**Features:**
- ✅ Finds all supported files in directory (recursive)
- ✅ Progress bar with percentage
- ✅ Parallel processing support
- ✅ Summary statistics (success rate, processing times)
- ✅ Error breakdown
- ✅ JSON result export

**Example Output:**
```
📂 Found 15 document(s)

✅ Using provider: gemini
✅ Using model: gemini-2.5-flash

🚀 Starting batch test...
============================================================

[████████████████████████████████████████] 100% (15/15) invoice_15.pdf

============================================================
📊 BATCH TEST SUMMARY
============================================================

Total Documents:     15
✅ Successful:       13
❌ Failed:           2
📈 Success Rate:     86.7%

⏱️  Processing Times:
   Average: 28.34s
   Min:     15.23s
   Max:     45.67s

❌ Error Breakdown:
   • Timeout: 1
   • Validation failed: 1

💾 Results saved to: results.json

⏱️  Total Time: 425.10s
```

---

## Testing Workflows

### Workflow 1: Test Backend Health

```bash
# 1. Start backend server
cd backend
uvicorn main:app --reload --port 8000

# 2. Run health check test (in another terminal)
pytest tests/test_integration.py::TestHealthEndpoint::test_health_check -v

# 3. Check health endpoint directly
curl http://localhost:8000/health
```

### Workflow 2: Test File Upload

```bash
# Using pytest
pytest tests/test_integration.py::TestUploadEndpoint::test_upload_valid_jpeg -v

# Using test script
python scripts/test_upload.py test_documents/sample.jpg
```

### Workflow 3: Test Complete Processing

```bash
# Using test script
python scripts/test_schema_parsing.py invoice.pdf --schema Invoice

# Expected flow:
# 1. Upload document → get file_id
# 2. Submit processing request → get job_id
# 3. Poll for status (pending → processing → success/error)
# 4. Display extracted data
```

### Workflow 4: Regression Testing

```bash
# Test entire directory of documents
python scripts/batch_test_parsing.py ./test_cases/ --schema Invoice --output test_results.json

# Check success rate
# - If < 80%: Investigate failures
# - If timeout errors: Increase --timeout or use faster model
# - If validation errors: Check schema definition
```

### Workflow 5: Test New Schema

```bash
# 1. Create custom schema via API
curl -X POST http://localhost:8000/api/schemas \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_schema",
    "description": "Test schema",
    "definition": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"}
      }
    }
  }'

# 2. Test with document
python scripts/test_schema_parsing.py doc.pdf --schema test_schema

# 3. Validate extracted data matches schema
```

---

## Test Data Organization

### Recommended Directory Structure

```
test_documents/
├── invoices/
│   ├── simple_invoice.pdf
│   ├── complex_invoice.pdf
│   └── handwritten_invoice.jpg
├── receipts/
│   ├── coffee_receipt.jpg
│   └── restaurant_receipt.png
├── id_cards/
│   ├── passport.jpg
│   └── drivers_license.png
└── edge_cases/
    ├── blurry_image.jpg
    ├── large_pdf.pdf
    └── low_quality.png
```

### Creating Test Documents

**For Invoice Testing:**
- Use real invoices with varying complexity
- Include handwritten notes
- Test different layouts

**For Receipt Testing:**
- Use thermal printed receipts
- Test faded receipts
- Include itemized receipts

**For Edge Cases:**
- Blurry images
- Low-resolution scans
- Large PDFs (10+ pages)
- Documents with watermarks
- Multiple languages

---

## Troubleshooting

### Tests Fail to Import Modules

**Error:** `ModuleNotFoundError: No module named 'services'`

**Solution:**
```bash
# Run tests from backend directory
cd backend
pytest tests/

# OR add backend to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

---

### Integration Tests Fail

**Error:** `ConnectionError` or `Connection refused`

**Solution:**
```bash
# Start backend server first
cd backend
uvicorn main:app --reload --port 8000

# Then run tests in another terminal
pytest tests/test_integration.py -v
```

---

### Test Scripts Can't Connect

**Error:** `❌ Error: Could not connect to backend`

**Solution:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Use correct URL
python scripts/test_upload.py file.pdf --url http://localhost:8000
```

---

### Timeout Errors

**Error:** `Processing timeout after 120 seconds`

**Solution:**
```bash
# Increase timeout for large documents
python scripts/test_schema_parsing.py large.pdf --schema Invoice --timeout 180

# Or use faster model
python scripts/test_schema_parsing.py doc.pdf --schema Invoice --model gemini-2.5-flash-lite
```

---

### No Providers Configured

**Error:** `No providers configured` or `404 Not Found` from providers API

**Solution:**
```bash
# Check .env file has API keys
cat .env | grep API_KEY

# List available providers
python scripts/test_schema_parsing.py --list-providers

# Add API key to .env:
# NEBIUS_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here
# OPENROUTER_API_KEY=your_key_here
```

---

### File Not Found Errors

**Error:** `File not found` during processing

**Solution:**
```bash
# Check file was uploaded successfully
python scripts/test_upload.py file.pdf

# Note the file_id returned

# Verify file exists in data/uploads/
ls data/uploads/

# Check database has file record
sqlite3 data/ocr_platform.db "SELECT * FROM uploaded_files ORDER BY id DESC LIMIT 5;"
```

---

### Database Locked Errors

**Error:** `database is locked` during tests

**Solution:**
```bash
# Stop backend server before running tests that access DB
# Or use in-memory database for tests:

export DATABASE_URL="sqlite:///:memory:"
pytest tests/
```

---

## Test Coverage

### Current Coverage

| Module | Coverage | Notes |
|--------|----------|-------|
| `schema_service.py` | ✅ High | 14 test cases |
| `image_service.py` | ✅ High | 18 test cases |
| Integration APIs | ✅ Medium | 17 test cases |
| VLM Providers | ⚠️ Low | Requires API keys |
| Processing Service | ⚠️ Medium | Some tests need mocking |

### Running Coverage Report

```bash
# Generate HTML coverage report
pytest tests/ --cov=services --cov-report=html

# Open report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## Best Practices

### 1. Use Descriptive Test Names

```python
# ✅ Good
def test_invoice_with_multiple_line_items_validates_correctly(self):

# ❌ Bad
def test_invoice(self):
```

### 2. Test Edge Cases

```python
# Test empty arrays
def test_schema_with_empty_array_field(self):

# Test missing optional fields
def test_schema_with_missing_optional_fields(self):

# Test maximum file size
def test_upload_exceeds_max_file_size(self):
```

### 3. Use Fixtures for Common Data

```python
@pytest.fixture
def sample_invoice_data(self):
    return {
        "invoice_number": "INV-001",
        "vendor_name": "Test Vendor",
        ...
    }

def test_validate_invoice(self, sample_invoice_data):
    result = validate_vlm_output(sample_invoice_data, schema)
```

### 4. Mock External Dependencies

```python
from unittest.mock import patch, AsyncMock

@patch('services.nebius.httpx.AsyncClient.post')
async def test_nebius_provider(mock_post):
    mock_post.return_value = AsyncMock(
        json=lambda: {"choices": [{"message": {"content": '{"text": "test"}"}]}
    )
    # Test provider logic without actual API calls
```

### 5. Clean Up Test Data

```python
@pytest.fixture(autouse=True)
def cleanup_test_data(self):
    # Setup
    yield
    # Cleanup: delete test files, database records, etc.
    test_files = Path("data/uploads").glob("test_*")
    for f in test_files:
        f.unlink()
```

---

## Quick Reference Commands

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_schema_service.py -v
```

### Run Specific Test
```bash
pytest tests/test_schema_service.py::TestSchemaValidation::test_validate_simple_object -v
```

### Run with Coverage
```bash
pytest tests/ --cov=services --cov-report=html
```

### Stop on First Failure
```bash
pytest tests/ -x
```

### Run Failed Tests Only
```bash
pytest tests/ --lf
```

### Verbose Output
```bash
pytest tests/ -vv -s
```

### Upload Test Document
```bash
python scripts/test_upload.py test.pdf
```

### Parse with Schema
```bash
python scripts/test_schema_parsing.py test.pdf --schema Invoice
```

### Batch Test Directory
```bash
python scripts/batch_test_parsing.py ./tests/ --schema Invoice --output results.json
```

---

## Additional Resources

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Main Testing Guide:** `docs/TESTING_GUIDE.md`
- **User Guide:** `docs/USER_GUIDE.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`

---

**Last Updated:** 2026-01-21
**Backend Version:** 1.0.0
**Python Version:** 3.11+
