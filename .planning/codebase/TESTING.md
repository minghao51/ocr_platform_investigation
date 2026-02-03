# Testing Guide

## Overview
The OCR Platform uses pytest for backend testing. Frontend testing is not currently implemented (manual testing only).

## Backend Testing

### Test Framework
- **pytest** - Test framework
- **pytest-asyncio** - Async test support
- **httpx** - HTTP client for testing FastAPI

### Test Structure
```
backend/tests/
├── __init__.py
├── test_integration.py      # End-to-end tests (323 lines)
├── test_schema_service.py   # Schema validation tests (292 lines)
├── test_image_service.py    # Image processing tests (276 lines)
└── test_fix_result_parsing.py # JSON parsing edge cases
```

### Running Tests

**All tests**:
```bash
cd backend
pytest
```

**Specific file**:
```bash
pytest tests/test_schema_service.py
```

**With coverage** (not currently configured):
```bash
pytest --cov=services --cov=routers
```

**Verbose output**:
```bash
pytest -v
```

---

## Test Categories

### 1. Integration Tests
**File**: `backend/tests/test_integration.py`

**Purpose**: End-to-end API testing

**Example**:
```python
@pytest.mark.asyncio
async def test_full_vision_pipeline():
    """Test complete vision extraction pipeline"""
    # Setup: Upload file
    # Action: Submit job
    # Assert: Job created successfully
    # Wait: Poll for completion
    # Assert: Result matches schema
```

**Coverage**:
- File upload
- Job submission
- Job status polling
- Result retrieval
- Both vision and text pipelines

---

### 2. Schema Service Tests
**File**: `backend/tests/test_schema_service.py`

**Purpose**: JSON schema validation

**Tests**:
- Builtin templates exist and are valid
- Data validation against schemas
- Edge cases (missing fields, wrong types)
- Double-encoded JSON handling

**Example**:
```python
def test_builtin_templates():
    templates = SchemaService.get_builtin_templates()
    assert "Invoice" in templates
    assert "Receipt" in templates

def test_validate_invoice():
    service = SchemaService()
    schema = templates["Invoice"]
    data = {"total": 100.00, "vendor": "Test"}
    is_valid, validated, error = service.validate_data(data, schema)
    assert is_valid is True
```

---

### 3. Image Service Tests
**File**: `backend/tests/test_image_service.py`

**Purpose**: Image processing

**Tests**:
- Image loading
- Resizing to target dimensions
- PDF to image conversion
- Base64 encoding
- RGBA to RGB conversion

**Example**:
```python
def test_resize_image():
    service = ImageService()
    img = Image.new("RGB", (2000, 2000))
    resized = service.resize_image(img, (1024, 1024))
    assert resized.size == (1024, 1024)
```

---

### 4. Edge Case Tests
**File**: `backend/tests/test_fix_result_parsing.py`

**Purpose**: Handle VLM response quirks

**Tests**:
- Double-encoded JSON
- Malformed JSON
- Missing required fields
- Extra fields not in schema

---

## Test Utilities

### Fixtures
**No shared fixtures** currently defined

**Could add**:
```python
@pytest.fixture
async def test_db():
    # Create test database
    # Run tests
    # Cleanup
    yield db

@pytest.fixture
def sample_image():
    # Return test image
    return Image.new("RGB", (1024, 1024))
```

---

### Test Client
**Usage pattern** (from integration tests):
```python
import httpx
from main import app

@pytest.mark.asyncio
async def test_api_endpoint():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/processing/upload", ...)
        assert response.status_code == 200
```

---

## Frontend Testing

### Current Status
**Not implemented** - Frontend is tested manually

### Recommended Setup (Future)
- **Vitest** - Test runner (Vite-native)
- **React Testing Library** - Component testing
- **MSW** - API mocking

### Example (Not Implemented)
```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import FileUpload from './FileUpload';

describe('FileUpload', () => {
  it('calls onFileSelect when file dropped', () => {
    const onFileSelect = vi.fn();
    render(<FileUpload onFileSelect={onFileSelect} />);

    // Simulate drop
    // Assert onFileSelect called
  });
});
```

---

## Manual Testing Procedures

### Backend Manual Testing
**Documented in**: `docs/development/backend-testing.md`

**Key scenarios**:
1. Upload JPEG/PNG images
2. Upload PDF documents
3. Test each provider (Nebius, OpenRouter, Gemini)
4. Verify schema validation
5. Test error handling (invalid files, missing API keys)

### Frontend Manual Testing
**Procedure**:
1. Start dev servers:
   ```bash
   cd backend && uv run uvicorn main:app --reload
   cd frontend && npm run dev
   ```
2. Open browser to `http://localhost:5173`
3. Test each extraction mode
4. Verify job history page
5. Test schema editor

---

## Test Coverage

### Current Coverage
**Not measured** - No coverage tool configured

### Estimated Coverage
Based on file analysis:
- **Services**: ~30% (only image, schema, integration)
- **Routers**: ~10% (only via integration tests)
- **Database**: ~20% (basic CRUD)
- **Frontend**: 0% (no automated tests)

### Gaps
- No unit tests for VLM providers
- No tests for document classifier
- No tests for text extraction service
- No tests for routers (upload, schemas, jobs)
- No frontend component tests
- No E2E tests (Playwright/Cypress)

---

## CI/CD Integration

### Current Status
**Not configured** - No GitHub Actions or CI pipeline

### Recommended Setup
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install uv
      - run: cd backend && uv sync
      - run: cd backend && pytest
```

---

## Testing Best Practices (Current)

### What Works Well
1. **Async tests** properly use `pytest.mark.asyncio`
2. **Integration tests** cover full request/response cycle
3. **Edge cases** tested for JSON parsing (double-encoding)
4. **Test data** created fresh each run (no shared state)

### Areas for Improvement
1. **Add fixtures** for common setup (test DB, sample images)
2. **Mock external APIs** (VLM providers) - currently make real calls
3. **Increase coverage** of services and routers
4. **Add frontend tests** for critical components
5. **Add E2E tests** for full user flows
6. **Measure coverage** with pytest-cov

---

## Mocking External Services

### Current Approach
**Real API calls** - Tests use actual provider API keys

**Problem**: Slow, requires credentials, costs money

**Recommended**:
```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_processing_with_mocked_provider():
    with patch('services.nebius.NebiusProvider') as mock_provider:
        instance = mock_provider.return_value.__aenter__.return_value
        instance.process_image = AsyncMock(
            return_value={"content": '{"total": 100}'}
        )

        result = await service.process_file(...)
        assert result["success"] is True
```

---

## Performance Testing

### Current Status
**Not implemented** - No performance benchmarks

### Recommended Tools
- **Locust** - Load testing API endpoints
- **pytest-benchmark** - Microbenchmarking functions

### Example Scenario
- Test max concurrent jobs
- Measure API response time
- Profile database queries

---

## Testing Documentation

### Test Reports
- `docs/development/auto-routing-test-report.md` - Document classifier testing

### Test Guides
- `docs/development/testing-guide.md` - General testing procedures
- `docs/development/backend-testing.md` - Backend-specific testing

---

## Common Test Patterns

### Async Service Test
```python
@pytest.mark.asyncio
async def test_service_method():
    service = ProcessingService()
    result = await service.process_file(
        file_id="test",
        file_path="test.jpg",
        file_type="image",
        provider_name="nebius",
        model="test-model",
        schema_definition={},
        prompt="Test"
    )
    assert result["success"] is True
```

### API Endpoint Test
```python
@pytest.mark.asyncio
async def test_api_endpoint():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
```

### Schema Validation Test
```python
def test_schema_validation():
    service = SchemaService()
    schema = {"type": "object", "properties": {...}}
    valid_data = {...}
    invalid_data = {...}

    is_valid, _, _ = service.validate_data(valid_data, schema)
    assert is_valid is True

    is_valid, _, error = service.validate_data(invalid_data, schema)
    assert is_valid is False
```

---

## Summary

| Aspect | Status |
|--------|--------|
| Backend Framework | pytest + pytest-asyncio |
| Frontend Framework | Not implemented |
| Integration Tests | Yes (test_integration.py) |
| Unit Tests | Partial (schema, image) |
| E2E Tests | No |
| Coverage Tracking | No |
| CI/CD | No |
| API Mocking | No (uses real calls) |
| Performance Tests | No |
