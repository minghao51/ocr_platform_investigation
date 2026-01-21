# OCR Platform - Testing Guide

Comprehensive guide for testing the OCR Platform, including manual testing procedures, automated tests, and validation strategies.

## Table of Contents

1. [Testing Overview](#testing-overview)
2. [Prerequisites for Testing](#prerequisites-for-testing)
3. [Manual Testing Checklist](#manual-testing-checklist)
4. [Automated Testing](#automated-testing)
5. [Test Data](#test-data)
6. [Expected Results](#expected-results)
7. [Performance Testing](#performance-testing)
8. [Reporting Issues](#reporting-issues)

---

## Testing Overview

### Testing Levels

1. **Smoke Tests** (5 min) - Quick health checks
2. **Functional Tests** (30 min) - Core feature validation
3. **Integration Tests** (1 hour) - End-to-end workflows
4. **Performance Tests** (30 min) - Load and timing validation
5. **Security Tests** (optional) - Input validation and error handling

### Testing Scope

- ✅ Backend API endpoints
- ✅ Frontend UI components
- ✅ VLM provider integrations
- ✅ Schema validation
- ✅ File upload handling
- ✅ Error handling
- ✅ Database operations
- ✅ Docker deployment

---

## Prerequisites for Testing

### 1. Application Setup

Before testing, ensure the application is running:

```bash
# Start with Docker (recommended)
docker compose up --build

# Or start locally (requires both backend and frontend)
# Terminal 1:
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2:
cd frontend && npm run dev
```

**Verify Application is Running**:
```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected","version":"1.0.0"}
```

### 2. API Keys

Configure at least one VLM provider in `.env`:

```bash
# Edit .env
NEBIUS_API_KEY=your_key_here
# OR
OPENROUTER_API_KEY=your_key_here
# OR
GEMINI_API_KEY=your_key_here
```

**Test API Key is Valid**:
```bash
# Check available providers
curl http://localhost:8000/api/providers

# Should return providers you have keys for
```

### 3. Test Documents

Prepare test documents (see [Test Data](#test-data) section):
- Sample images (JPG, PNG)
- Sample PDFs (single and multi-page)
- Edge case files (large files, unusual formats)

### 4. Testing Tools

**Optional but Recommended**:
- **Postman** or **Insomnia**: For API testing
- **Browser DevTools**: For frontend debugging
- **SQLite Browser**: For database inspection

---

## Manual Testing Checklist

### Phase 1: Smoke Tests (5 minutes)

Quick checks to ensure basic functionality works.

#### Test 1.1: Application Health
- [ ] Access http://localhost:8000
- [ ] Verify page loads without errors
- [ ] Check browser console for errors (F12 → Console)
- [ ] Verify navigation works (Process ↔ History)

**Expected**: Clean page load, no console errors

#### Test 1.2: API Health
- [ ] Visit http://localhost:8000/health
- [ ] Visit http://localhost:8000/docs
- [ ] Check Swagger UI loads

**Expected**:
```json
{"status":"healthy","database":"connected","version":"1.0.0"}
```

#### Test 1.3: Providers Available
- [ ] Visit http://localhost:8000/api/providers
- [ ] Verify at least one provider is listed
- [ ] Check models are listed under each provider

**Expected**:
```json
{
  "nebius": {
    "models": ["meta-llama/Meta-Llama-3.2-11B-Vision-Instruct"]
  }
}
```

---

### Phase 2: Functional Tests (30 minutes)

#### Test 2.1: File Upload - Valid Images

**Steps**:
1. Navigate to **Process** page
2. Upload a valid JPG image (≤ 10MB)
3. Verify file name appears
4. Verify no error messages

**Expected**:
- File uploads successfully
- File preview shows file name
- Ready to select model and schema

**Test Data**: Use any clear JPG/PNG image

**Test Cases**:
- [ ] JPG format
- [ ] PNG format
- [ ] Small file (< 1MB)
- [ ] Large file (5-10MB)

#### Test 2.2: File Upload - Invalid Files

**Steps**:
1. Try uploading an unsupported file type (e.g., .txt, .mp4)
2. Try uploading a file > 10MB
3. Verify appropriate error messages

**Expected**:
- Clear error message
- File rejected
- No crash or hanging

**Test Cases**:
- [ ] Text file (.txt)
- [ ] Video file (.mp4)
- [ ] Large file (> 10MB)
- [ ] Corrupted image

#### Test 2.3: PDF Upload

**Steps**:
1. Upload a single-page PDF
2. Upload a multi-page PDF (3-5 pages)
3. Verify processing works

**Expected**:
- PDF uploads successfully
- Processing completes
- Results extracted

**Test Cases**:
- [ ] Single-page PDF
- [ ] Multi-page PDF
- [ ] Scanned PDF (image-based)

#### Test 2.4: Model Selection

**Steps**:
1. Select each available provider
2. Verify models populate correctly
3. Try processing with each model

**Expected**:
- Models list appears
- Selection works
- Processing completes

**Test Cases**:
- [ ] Nebius provider
- [ ] OpenRouter provider
- [ ] Gemini provider

#### Test 2.5: Built-in Schema Templates

**Steps**:
1. Select each built-in template
2. Upload appropriate document
3. Process and verify results

**Test Cases**:
- [ ] **Invoice** template with invoice document
- [ ] **Receipt** template with receipt
- [ ] **ID Card** template with ID card
- [ ] **Generic Document** template with article

**Expected**:
- Schema loads correctly
- JSON preview shows in editor
- Results match schema structure

#### Test 2.6: Custom Schema Creation

**Steps**:
1. Click "Custom Schema" button
2. Enter simple JSON schema:
   ```json
   {
     "type": "object",
     "properties": {
       "title": {"type": "string"},
       "author": {"type": "string"}
     },
     "required": ["title"]
   }
   ```
3. Save custom schema
4. Process document with custom schema

**Expected**:
- Schema validates successfully
- Data extracted according to schema
- Results display correctly

#### Test 2.7: Processing Workflow

**End-to-End Test**:

1. Upload document (invoice image)
2. Select provider (Gemini)
3. Select model (gemini-1.5-flash)
4. Select schema (Invoice)
5. Click "Process Document"
6. Monitor status updates
7. Review results
8. Copy results to clipboard

**Expected Flow**:
```
Upload → Select → Process → Pending → Processing → Success → Results
```

**Expected Results**:
- Status updates every 2 seconds
- Processing completes in 5-30 seconds
- JSON results displayed
- Copy button works

#### Test 2.8: History and Job Management

**Steps**:
1. Process 3-5 documents
2. Navigate to **History** page
3. Verify jobs appear in list
4. Test filters:
   - All Jobs
   - Success Only
   - Errors Only
   - By Provider
5. Click "View" on a job
6. Click "Delete" on a job

**Expected**:
- All jobs listed
- Filters work correctly
- Job details show in modal
- Delete removes job permanently

#### Test 2.9: Error Handling

**Test Invalid API Key**:
1. Temporarily set invalid API key in `.env`
2. Restart application
3. Try processing document
4. Verify error message is clear

**Expected**:
- Error message displayed
- No crash or hang
- Useful error details

**Test Schema Validation Failure**:
1. Create schema that likely won't match
2. Process document
3. Verify validation error shown

**Expected**:
- Clear error about schema mismatch
- Raw VLM response shown (optional)
- Helpful suggestions

---

### Phase 3: Integration Tests (1 hour)

#### Test 3.1: Database Persistence

**Steps**:
1. Process a document
2. Stop application
3. Restart application
4. Navigate to History
5. Verify job still exists

**Expected**:
- Job persists across restarts
- Database stored in `data/ocr_platform.db`

#### Test 3.2: Schema CRUD Operations

**Test with API**:

```bash
# List all schemas
curl http://localhost:8000/api/schemas

# Get templates only
curl http://localhost:8000/api/schemas?is_template=true

# Create custom schema
curl -X POST http://localhost:8000/api/schemas \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_schema",
    "description": "Test schema",
    "definition": {
      "type": "object",
      "properties": {
        "field1": {"type": "string"}
      }
    }
  }'

# Get specific schema
curl http://localhost:8000/api/schemas/1
```

**Expected**:
- Schemas listed
- Templates marked with `is_template: true`
- Custom schema created successfully
- Schema retrieved by ID

#### Test 3.3: Job Operations

**Test with API**:

```bash
# List all jobs
curl http://localhost:8000/api/jobs

# Filter by status
curl http://localhost:8000/api/jobs?status=success

# Filter by provider
curl http://localhost:8000/api/jobs?provider=nebius

# Get job details
curl http://localhost:8000/api/jobs/1

# Delete job
curl -X DELETE http://localhost:8000/api/jobs/1
```

**Expected**:
- Jobs listed with pagination
- Filters work correctly
- Job details include all metadata
- Delete removes job

#### Test 3.4: Upload and Process Integration

**Test Complete Workflow via API**:

```bash
# Step 1: Upload file
UPLOAD_RESPONSE=$(curl -X POST http://localhost:8000/api/upload \
  -F "file=@test_invoice.jpg")

# Extract file_id from response
FILE_ID=$(echo $UPLOAD_RESPONSE | jq -r '.file_id')

# Step 2: Start processing
curl -X POST http://localhost:8000/api/process \
  -H "Content-Type: application/json" \
  -d "{
    \"file_id\": \"$FILE_ID\",
    \"provider\": \"gemini\",
    \"model\": \"gemini-1.5-flash\",
    \"schema_name\": \"Invoice\"
  }"

# Step 3: Poll for status (replace JOB_ID)
JOB_ID="<from previous response>"
curl http://localhost:8000/api/process/status/$JOB_ID

# Repeat until status is "success" or "error"
```

**Expected**:
- File upload returns file_id
- Processing returns job_id
- Status polling shows progress
- Final status is success with results

---

### Phase 4: Performance Tests (30 minutes)

#### Test 4.1: Processing Speed

**Test Procedure**:
1. Process 10 documents (same type)
2. Record processing time for each
3. Calculate average and median

**Expected Performance**:
- Single-page images: 3-10 seconds
- Multi-page PDFs (5 pages): 15-60 seconds
- Average: < 15 seconds for typical documents

**Test Results Template**:
```
Document Type | Model | Time (s) | Status
-------------|-------|----------|--------
Invoice JPG  | gemini-flash | 4.2 | Success
Receipt PNG  | claude-3.5 | 6.1 | Success
5-page PDF   | gemini-pro | 32.5 | Success
```

#### Test 4.2: Concurrent Processing

**Test Procedure**:
1. Open 3 browser tabs
2. Start processing in each tab simultaneously
3. Monitor for errors or slowdowns

**Expected**:
- All jobs complete successfully
- No database locks
- Status polling works for all jobs

#### Test 4.3: Large File Handling

**Test Cases**:
- [ ] 8MB PDF
- [ ] 10MB PDF (max size)
- [ ] 10-page PDF

**Expected**:
- Files near 10MB limit process successfully
- No memory errors
- Processing completes

---

### Phase 5: Edge Cases (15 minutes)

#### Test 5.1: Empty/Blank Documents

**Steps**:
1. Process blank white image
2. Process image with no text

**Expected**:
- Processing completes
- Returns empty results or appropriate message
- No crash

#### Test 5.2: Low Quality Images

**Test Cases**:
- [ ] Very blurry image
- [ ] Very dark image
- [ ] Low resolution (< 500px)
- [ ] Handwritten text

**Expected**:
- Processing completes but may return low-quality results
- No crash
- Graceful degradation

#### Test 5.3: Special Characters in Text

**Test Cases**:
- [ ] Documents with emojis
- [ ] Documents with Unicode characters
- [ ] Documents with right-to-left text (Arabic, Hebrew)

**Expected**:
- Special characters preserved
- No encoding errors
- JSON properly escaped

#### Test 5.4: Malformed Schemas

**Steps**:
1. Enter invalid JSON in schema editor
2. Try processing

**Expected**:
- Clear validation error
- Schema rejected before processing
- No API call made

---

## Automated Testing

### Unit Tests

**Backend Unit Tests** (to be implemented):

```bash
# Run all tests
cd backend
pytest tests/

# Run specific test file
pytest tests/test_schema_service.py

# Run with coverage
pytest --cov=services --cov-report=html
```

**Test Coverage Goals**:
- Schema validation: 90%+
- Image processing: 80%+
- Provider adapters: 75%+

### Integration Tests

**API Integration Tests** (to be implemented):

```bash
# Run integration tests
cd backend
pytest tests/integration/

# Requires test database and mock VLM APIs
```

**Test Scenarios**:
1. Upload → Process → Status → Results workflow
2. Schema CRUD operations
3. Job lifecycle management
4. Error handling endpoints

### Frontend Tests

**Frontend Component Tests** (to be implemented):

```bash
cd frontend
npm test
```

**Test Components**:
- FileUpload component
- ModelSelector component
- SchemaEditor component
- ResultsDisplay component

---

## Test Data

### Sample Documents

Create or download these test documents:

#### 1. Invoice (JPG/PDF)
- Clear invoice with:
  - Invoice number
  - Vendor name and address
  - Line items (3-5 items)
  - Subtotal, tax, total
  - Date

#### 2. Receipt (JPG/PNG)
- Store or restaurant receipt with:
  - Merchant name
  - Transaction date
  - Item list
  - Total amount

#### 3. ID Card (JPG/PNG)
- Driver's license or ID card with:
  - Full name
  - Date of birth
  - Document number
  - Address
  - Expiration date

#### 4. Generic Document (PDF)
- 2-3 page article or report with:
  - Title
  - Multiple paragraphs
  - Named entities (people, organizations, dates)

#### 5. Edge Cases
- Blank document
- Very blurry document
- Document with handwriting
- Document in foreign language

### Test Schemas

#### Simple Schema
```json
{
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "value": {"type": "number"}
  },
  "required": ["name"]
}
```

#### Nested Schema
```json
{
  "type": "object",
  "properties": {
    "person": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "age": {"type": "number"}
      }
    },
    "address": {
      "type": "object",
      "properties": {
        "street": {"type": "string"},
        "city": {"type": "string"}
      }
    }
  }
}
```

#### Array Schema
```json
{
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "quantity": {"type": "number"}
        }
      }
    }
  }
}
```

---

## Expected Results

### Successful Processing Response

```json
{
  "success": true,
  "job_id": "uuid-here",
  "status": "success",
  "result": {
    "invoice_number": "INV-001",
    "vendor_name": "Acme Corp",
    "total_amount": 150.00
  },
  "processing_time_seconds": 4.2,
  "provider": "nebius",
  "model": "meta-llama/Meta-Llama-3.2-11B-Vision-Instruct",
  "schema_name": "Invoice"
}
```

### Error Response

```json
{
  "success": false,
  "status": "error",
  "error_code": "VLM_API_ERROR",
  "message": "API request failed",
  "details": {
    "provider": "nebius",
    "raw_error": "Invalid API key"
  }
}
```

---

## Performance Benchmarks

### Expected Performance

| Document Type | Size | Model | Expected Time |
|--------------|------|-------|---------------|
| Single-page image | < 1MB | gemini-flash | 3-5s |
| Single-page image | < 1MB | claude-3.5 | 5-10s |
| Single-page image | < 1MB | llama-3.2 | 4-8s |
| Multi-page PDF | 5 pages | gemini-pro | 20-40s |
| Multi-page PDF | 5 pages | gemini-flash | 15-30s |

### Performance Test Template

```
Date: ___________
Tester: ___________

Test Document: ___________
File Size: ___________
File Type: ___________

Model: ___________
Provider: ___________

Processing Time: ___________ seconds
Status: ___________

Quality Assessment:
- All fields extracted: [ ] Yes [ ] No
- Accuracy: [ ] Excellent [ ] Good [ ] Fair [ ] Poor
- Errors: ___________

Notes: ___________
```

---

## Reporting Issues

### Bug Report Template

```markdown
**Title**: [Brief description of issue]

**Environment**:
- OS: [Mac/Linux/Windows]
- Browser: [Chrome/Firefox/Safari]
- Docker: [Yes/No]
- Provider: [Nebius/OpenRouter/Gemini]

**Steps to Reproduce**:
1.
2.
3.

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happened]

**Screenshots**:
[If applicable]

**Logs**:
```
[Paste relevant logs here]
```

**Additional Context**:
[Any other information]
```

### Common Issues and Solutions

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| "API key not found" | Missing .env file | Create .env with API keys |
| "Database locked" | Multiple writes | Restart application |
| "Port 8000 in use" | Conflicting service | Stop other service or change port |
| "Processing timeout" | Large file or slow API | Use smaller file or faster model |
| "Schema validation failed" | VLM output mismatch | Simplify schema or try different model |

---

## Test Execution Summary

### Quick Test Run (15 minutes)
1. Smoke tests (5 min)
2. Upload + process 1 document (5 min)
3. Check history (5 min)

### Full Test Run (2 hours)
1. Smoke tests (5 min)
2. Functional tests (30 min)
3. Integration tests (60 min)
4. Performance tests (30 min)
5. Edge cases (15 min)

### Continuous Testing
- Run smoke tests before each commit
- Run full tests before releases
- Monitor performance in production

---

## Testing Checklist Summary

### Before Deploying
- [ ] All smoke tests pass
- [ ] All functional tests pass
- [ ] At least one VLM provider tested
- [ ] All built-in schemas tested
- [ ] Custom schema tested
- [ ] File upload tested for all supported types
- [ ] Error handling tested
- [ ] Database persistence verified
- [ ] Performance acceptable
- [ ] Documentation updated

### After Changes
- [ ] Relevant tests re-run
- [ ] New features tested
- [ ] Regression testing done
- [ ] Documentation updated

---

**Last Updated**: 2026-01-16
**Version**: 1.0.0
**Status**: Ready for Testing
