# OCR Platform - Troubleshooting Guide

Comprehensive troubleshooting guide for common issues, errors, and their solutions.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Docker Issues](#docker-issues)
4. [Backend Issues](#backend-issues)
5. [Frontend Issues](#frontend-issues)
6. [API Key Issues](#api-key-issues)
7. [Processing Issues](#processing-issues)
8. [Database Issues](#database-issues)
9. [Performance Issues](#performance-issues)
10. [Error Codes Reference](#error-codes-reference)

---

## Quick Diagnostics

### Health Check Script

Run these commands to diagnose issues:

```bash
# 1. Check if application is running
curl http://localhost:8000/health

# Expected: {"status":"healthy","database":"connected","version":"1.0.0"}

# 2. Check Docker containers (if using Docker)
docker ps

# Should show: ocr_platform container running

# 3. Check backend logs (Docker)
docker compose logs --tail 50

# 4. Check database file exists
ls -lh data/ocr_platform.db

# 5. Check available providers
curl http://localhost:8000/api/providers

# Should return: {"nebius": {...}, "openrouter": {...}, "gemini": {...}}
```

### Browser Console Diagnostics

Open browser DevTools (F12) and check:

**Console Tab**:
- Red error messages
- Failed network requests
- JavaScript errors

**Network Tab**:
- API calls to `/api/*`
- Status codes (should be 200 or 201)
- Response times

---

## Installation Issues

### Issue: "python: command not found"

**Symptoms**:
```bash
python: command not found
```

**Cause**: Python not installed or not in PATH

**Solutions**:

1. **Install Python**:
   - **Mac**: `brew install python3`
   - **Ubuntu**: `sudo apt-get install python3.11`
   - **Windows**: Download from https://www.python.org/downloads/

2. **Use python3 instead**:
   ```bash
   python3 --version
   ```

3. **Add to PATH** (Windows):
   - Search "Environment Variables"
   - Add Python installation directory to PATH

### Issue: "pip: command not found"

**Symptoms**:
```bash
pip: command not found
```

**Solutions**:

1. **Ensure Python is installed**:
   ```bash
   python3 -m pip --version
   ```

2. **Use python -m pip**:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **Install pip**:
   ```bash
   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   python3 get-pip.py
   ```

### Issue: "npm: command not found"

**Symptoms**:
```bash
npm: command not found
```

**Solutions**:

1. **Install Node.js** (includes npm):
   - **Mac**: `brew install node`
   - **Ubuntu**: `sudo apt-get install nodejs npm`
   - **Windows**: Download from https://nodejs.org/

2. **Verify installation**:
   ```bash
   node --version
   npm --version
   ```

### Issue: Module installation fails

**Symptoms**:
```bash
ERROR: Could not build wheels for pillow
```

**Cause**: Missing system dependencies

**Solutions**:

**Mac**:
```bash
brew install python-tk@3.11
```

**Ubuntu/Debian**:
```bash
sudo apt-get update
sudo apt-get install python3-dev python3-pip libpng-dev libjpeg-dev
```

**Windows**:
- Install Microsoft Visual C++ Build Tools
- Download from: https://visualstudio.microsoft.com/downloads/

---

## Docker Issues

### Issue: "docker: command not found"

**Cause**: Docker not installed

**Solution**:
1. Download Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Verify: `docker --version`

### Issue: "Cannot connect to the Docker daemon"

**Symptoms**:
```bash
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Cause**: Docker daemon not running

**Solutions**:

1. **Start Docker Desktop**:
   - **Mac**: Open Docker from Applications
   - **Windows**: Start Docker Desktop from Start Menu

2. **Check Docker status**:
   ```bash
   docker info
   ```

3. **Restart Docker**:
   - Quit Docker Desktop completely
   - Reopen Docker Desktop
   - Wait for "Docker is running" message

### Issue: Port 8000 already in use

**Symptoms**:
```bash
Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solutions**:

**Option 1**: Kill process using port 8000
```bash
# Find process
lsof -i :8000

# Kill it
kill -9 <PID>
```

**Option 2**: Change port in `docker-compose.yml`:
```yaml
services:
  app:
    ports:
      - "8001:8000"  # Use localhost:8001 instead
```

### Issue: Container exits immediately

**Symptoms**:
Container starts but exits immediately

**Diagnosis**:
```bash
docker compose logs
```

**Common Causes**:

1. **Missing .env file**:
   ```bash
   cp .env.example .env
   # Edit .env with API keys
   ```

2. **Invalid API keys format**:
   - Ensure no extra quotes
   - Ensure no spaces around `=`
   - Example: `GEMINI_API_KEY=AIzaYourKey` (not `"GEMINI_API_KEY=..."`)

3. **Database permission error**:
   ```bash
   mkdir -p data
   chmod 777 data
   ```

### Issue: Build fails during docker compose up

**Symptoms**:
```bash
ERROR [build stage] Failed to build
```

**Solutions**:

1. **Rebuild without cache**:
   ```bash
   docker compose build --no-cache
   ```

2. **Check disk space**:
   ```bash
   df -h
   # Need at least 5GB free
   ```

3. **Clear Docker cache**:
   ```bash
   docker system prune -a
   ```

---

## Backend Issues

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Cause**: Dependencies not installed

**Solution**:
```bash
cd backend
pip install -r requirements.txt
```

### Issue: Database initialization fails

**Symptoms**:
```bash
sqlite3.OperationalError: no such table: schemas
```

**Solution**:
```bash
cd backend
python -m database.migrations
```

**Expected output**:
```
✅ Database initialized at: sqlite:///./data/ocr_platform.db
✅ Created tables: schemas, processing_jobs
✅ Inserted 4 template schemas
```

### Issue: Port 8000 in use (local development)

**Symptoms**:
```bash
ERROR: [Errno 48] Address already in use
```

**Solutions**:

**Option 1**: Kill process
```bash
lsof -i :8000
kill -9 <PID>
```

**Option 2**: Use different port
```bash
uvicorn main:app --port 8001
```

### Issue: Import errors

**Symptoms**:
```bash
ImportError: cannot import name 'X' from 'Y'
```

**Solution**:
1. Ensure you're in backend directory
2. Check Python path:
   ```bash
   cd backend
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   uvicorn main:app --reload
   ```

---

## Frontend Issues

### Issue: "Cannot find module 'react'"

**Cause**: Node dependencies not installed

**Solution**:
```bash
cd frontend
npm install
```

### Issue: Port 5173 already in use

**Symptoms**:
```bash
Port 5173 is in use, trying another one...
```

**Solutions**:

**Option 1**: Kill process
```bash
lsof -i :5173
kill -9 <PID>
```

**Option 2**: Let Vite use another port
- Vite will automatically try 5174, 5175, etc.

### Issue: Blank page or "Failed to fetch"

**Symptoms**:
- Page loads blank
- Browser console shows "Failed to fetch"

**Cause**: Backend not running or CORS issue

**Solutions**:

1. **Check backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **If running locally**, add CORS to backend or use proxy:
   - Edit `frontend/vite.config.ts`:
   ```typescript
   export default defineConfig({
     server: {
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true,
         },
       },
     },
   })
   ```

3. **Clear browser cache**:
   - Ctrl+Shift+R (Windows/Linux)
   - Cmd+Shift+R (Mac)

### Issue: Build fails with TypeScript errors

**Symptoms**:
```bash
TS2345: Argument of type 'X' is not assignable to parameter of type 'Y'
```

**Solution**:
1. Check error details
2. Fix type annotations in `.tsx` files
3. Or temporarily disable strict mode in `tsconfig.json`

---

## API Key Issues

### Issue: "API key not configured for provider"

**Symptoms**:
```json
{
  "error": "API key not configured for provider: nebius"
}
```

**Cause**: API key missing from `.env`

**Solution**:
1. Open `.env` file
2. Add API key:
   ```env
   NEBIUS_API_KEY=your-actual-key-here
   ```
3. Restart application

### Issue: "401 Unauthorized" from VLM provider

**Cause**: Invalid API key

**Solutions**:

1. **Verify API key is correct**:
   - Check for typos
   - Regenerate from provider dashboard

2. **Check for extra characters**:
   ```bash
   # Wrong (has quotes)
   NEBIUS_API_KEY="sk-abc123"

   # Correct
   NEBIUS_API_KEY=sk-abc123
   ```

3. **Test API key manually**:
   ```bash
   # Test Gemini key
   curl -H "x-goog-api-key: YOUR_KEY" \
     "https://generativelanguage.googleapis.com/v1beta/models"
   ```

### Issue: "429 Too Many Requests"

**Symptoms**:
```json
{
  "error": "Rate limit exceeded"
}
```

**Cause**: Hit provider rate limit

**Solutions**:

1. **Wait a few minutes** before retrying

2. **Check rate limits**:
   - **Gemini Free**: 15 requests/minute
   - **OpenRouter**: Varies by model
   - **Nebius**: Varies by plan

3. **Upgrade plan** (if hitting limits frequently)

4. **Add retry logic** (for production use)

---

## Processing Issues

### Issue: Processing stuck at "Processing..."

**Symptoms**: Status never changes from "processing"

**Diagnosis**:
```bash
# Check backend logs
docker compose logs -f backend

# Or check job status
curl http://localhost:8000/api/process/status/<job_id>
```

**Possible Causes**:

1. **VLM API timeout**:
   - Large documents take longer
   - Provider is slow
   - Solution: Wait longer or use faster model

2. **API error occurred**:
   - Check logs for error details
   - Verify API key is valid

3. **Database lock**:
   - Restart application
   - Check for multiple instances

### Issue: "SCHEMA_VALIDATION_FAILED"

**Symptoms**:
```json
{
  "error_code": "SCHEMA_VALIDATION_FAILED",
  "message": "VLM output did not match the required schema"
}
```

**Cause**: VLM output doesn't match schema structure

**Solutions**:

1. **Simplify schema**:
   - Remove optional fields
   - Use simpler types (string instead of nested objects)

2. **Try different model**:
   - Some models follow instructions better than others
   - Try Claude 3.5 or GPT-4o

3. **Add descriptions** to schema fields:
   ```json
   {
     "type": "object",
     "properties": {
       "invoice_number": {
         "type": "string",
         "description": "The invoice number typically labeled as 'Invoice No.' or 'Invoice #'"
       }
     }
   }
   ```

4. **Check raw VLM response** in error details:
   - See what VLM actually returned
   - Adjust schema to match

### Issue: "VLM_INVALID_JSON"

**Symptoms**:
```json
{
  "error_code": "VLM_INVALID_JSON",
  "message": "VLM did not return valid JSON"
}
```

**Cause**: VLM didn't return JSON format

**Solutions**:

1. **Try different model** (some are better at JSON output)

2. **Use Generic schema** first to see what model returns

3. **Check if document has extractable text**

### Issue: Poor extraction quality

**Symptoms**: Extraction succeeds but data is incomplete or wrong

**Solutions**:

1. **Improve image quality**:
   - Use higher resolution scan
   - Ensure good lighting
   - Straighten document alignment

2. **Try different model**:
   - Claude 3.5 Sonnet: Best for complex layouts
   - Gemini 1.5 Pro: Best overall accuracy
   - GPT-4o: Good general performance

3. **Simplify schema**:
   - Fewer fields = better accuracy
   - Focus on critical data only

4. **Process multi-page PDFs page by page**:
   - Split PDF into single pages
   - Process each separately

---

## Database Issues

### Issue: "Database is locked"

**Symptoms**:
```bash
sqlite3.OperationalError: database is locked
```

**Cause**: Multiple processes writing to database

**Solutions**:

1. **Stop all applications**:
   ```bash
   docker compose down
   ```

2. **Remove lock files**:
   ```bash
   rm data/ocr_platform.db-shm
   rm data/ocr_platform.db-wal
   ```

3. **Restart**:
   ```bash
   docker compose up
   ```

### Issue: "Database disk image is malformed"

**Cause**: Database file corrupted

**Solutions**:

**Option 1**: Reinitialize database
```bash
# Backup (if possible)
cp data/ocr_platform.db data/ocr_platform.db.backup

# Remove and recreate
rm data/ocr_platform.db
docker compose up  # Will auto-initialize
```

**Option 2**: Dump and restore
```bash
# Dump data
sqlite3 data/ocr_platform.db .dump > backup.sql

# Create new database
sqlite3 data/ocr_platform_new.db < backup.sql

# Replace old database
mv data/ocr_platform_new.db data/ocr_platform.db
```

---

## Performance Issues

### Issue: Processing is very slow (> 60 seconds)

**Diagnosis**:
```bash
# Check processing time in job result
curl http://localhost:8000/api/jobs/1
# Look for "processing_time_seconds"
```

**Solutions**:

1. **Use faster model**:
   - Gemini 1.5 Flash (fastest)
   - Llama 3.2 Vision (fast)

2. **Reduce image size**:
   - Resize large images before uploading
   - Keep images < 2MB if possible

3. **Process fewer pages**:
   - Split multi-page PDFs
   - Process in batches

4. **Check internet connection**:
   - Slow network = slow API calls

### Issue: High memory usage

**Symptoms**: Container using > 2GB RAM

**Solutions**:

1. **Limit Docker memory**:
   - Docker Desktop → Settings → Resources → Memory
   - Set to 4GB or less

2. **Process smaller batches**:
   - Don't upload multiple files simultaneously

3. **Restart container periodically**:
   ```bash
   docker compose restart
   ```

---

## Error Codes Reference

| Error Code | Description | Common Cause | Solution |
|-----------|-------------|--------------|----------|
| `INVALID_FILE_TYPE` | File format not supported | Uploaded .txt, .mp4, etc. | Use JPG, PNG, GIF, WebP, or PDF |
| `FILE_TOO_LARGE` | File exceeds 10MB | Large PDF or high-res image | Compress or split file |
| `INVALID_JSON` | Malformed JSON in schema | Syntax error in schema | Fix JSON syntax in schema editor |
| `INVALID_PYDANTIC_SCHEMA` | Invalid schema definition | Schema not valid JSON Schema | Check schema format |
| `SCHEMA_VALIDATION_FAILED` | VLM output doesn't match schema | VLM returned wrong structure | Simplify schema or try different model |
| `VLM_API_ERROR` | Provider API error | Invalid key, network issue | Check API key and internet |
| `VLM_INVALID_JSON` | VLM didn't return JSON | Model didn't follow instructions | Try model better at JSON |
| `VLM_TIMEOUT` | Request took too long | Large file or slow provider | Use faster model or smaller file |
| `VLM_RATE_LIMITED` | Hit provider rate limit | Too many requests | Wait and retry |
| `DATABASE_ERROR` | Database operation failed | Lock or corruption | Restart application |

---

## Getting Help

### Before Asking for Help

1. **Check logs**:
   ```bash
   docker compose logs --tail 100
   ```

2. **Run health check**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Review error messages**:
   - Browser console (F12)
   - Backend logs
   - API response

4. **Try fresh start**:
   ```bash
   docker compose down -v
   docker compose up --build
   ```

### Useful Commands

```bash
# View real-time logs
docker compose logs -f

# Restart container
docker compose restart

# Rebuild from scratch
docker compose down
docker compose build --no-cache
docker compose up

# Check database
sqlite3 data/ocr_platform.db "SELECT * FROM processing_jobs LIMIT 5;"

# Test API manually
curl http://localhost:8000/api/providers
curl http://localhost:8000/api/schemas?is_template=true
```

### When to Contact Support

- Multiple attempts at solutions failed
- Error messages unclear
- Performance consistently poor
- Need help with custom schemas

---

**Last Updated**: 2026-01-16
**Version**: 1.0.0
