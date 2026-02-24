# Data Flow

## Authentication Flow
1. User submits credentials to `/api/auth/login`
2. Backend verifies password via `auth.py:verify_password()`
3. JWT token created via `auth.py:create_access_token()`
4. Frontend stores token in localStorage
5. Subsequent requests include `Authorization: Bearer <token>`

## Document Processing Flow
1. **Upload**: File sent to `/api/upload` → saved to `backend/data/uploads/`
2. **Classification**: `document_classifier.py` determines processing method
   - Digital PDF → Text extraction (pdfplumber)
   - Scanned PDF/Image → Vision processing (VLM)
3. **Extraction**:
   - Text: `text_extraction.py` extracts text from PDF
   - Vision: `vlm_provider.py` calls selected VLM (Nebius/OpenRouter/Gemini)
4. **Schema Validation**: `schema_service.py` validates output against schema
5. **Result**: Job status updated, results stored in SQLite

## Job Tracking
- Jobs stored in `jobs` table with status: pending/processing/completed/failed
- Frontend polls `/api/jobs/{id}` for status updates
- WebSocket available at `/ws/jobs/{id}` for real-time updates
