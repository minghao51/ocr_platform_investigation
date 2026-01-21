# OCR Platform MVP

A modern OCR (Optical Character Recognition) platform that uses Vision Language Models (VLMs) to extract structured data from documents. Supports multiple VLM providers including Nebius, OpenRouter, and Google Gemini.

## Features

- **Multiple VLM Providers**: Support for Nebius (Llama 3.2), OpenRouter (Claude, GPT-4o, Gemini), and Google Gemini 1.5
- **Document Formats**: Process images (JPEG, PNG, GIF, WebP) and PDFs
- **Schema-Based Extraction**: Define custom JSON schemas for structured data extraction
- **Built-in Templates**: Pre-configured schemas for Invoices, Receipts, ID cards, and Generic documents
- **Real-Time Processing**: Background job processing with status polling
- **Job History**: Track and review all processing jobs
- **Modern UI**: React-based frontend with Tailwind CSS

## Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Pydantic v2**: Data validation and settings management
- **aiosqlite**: Async SQLite database
- **pdf2image**: PDF to image conversion
- **httpx**: Async HTTP client for VLM APIs

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **TailwindCSS**: Utility-first CSS framework

### Infrastructure
- **Docker**: Multi-stage builds for optimized images
- **Docker Compose**: Local development and deployment

## 📚 Documentation

**Comprehensive guides available in the `docs/` directory:**

| Document | Description | Link |
|----------|-------------|------|
| **Setup Guide** | Complete setup instructions for Docker and local development | [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md) |
| **User Guide** | How to use the platform, create schemas, understand results | [docs/USER_GUIDE.md](docs/USER_GUIDE.md) |
| **Testing Guide** | Manual and automated testing procedures | [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) |
| **Troubleshooting** | Diagnose and fix common issues | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| **Schema Guide** | Create custom JSON schemas for extraction | [SCHEMA_GUIDE.md](SCHEMA_GUIDE.md) |
| **Implementation Report** | Technical implementation details | [docs/IMPLEMENTATION_COMPLETE.md](docs/IMPLEMENTATION_COMPLETE.md) |

**New users**: Start with the [Setup Guide](docs/SETUP_GUIDE.md)

## Quick Start

### Prerequisites

- Docker and Docker Compose installed (or Python 3.11+ and Node 18+ for local development)
- API keys for at least one VLM provider

### Step-by-Step Setup

📖 **For detailed instructions, see [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)**

#### 1. Configure Environment

### Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```env
NEBIUS_API_KEY=your_nebius_key
OPENROUTER_API_KEY=your_openrouter_key
GEMINI_API_KEY=your_gemini_key
```

### Running with Docker (Recommended)

```bash
# Build and start the application
docker compose up --build

# The application will be available at http://localhost:8000
```

### Running Locally (Development)

#### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m database.migrations

# Run development server
uvicorn main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Frontend available at http://localhost:5173
```

## 🚀 Usage

📖 **For detailed usage instructions, see [docs/USER_GUIDE.md](docs/USER_GUIDE.md)**

### Basic Workflow

1. **Upload Document** (JPEG, PNG, GIF, WebP, or PDF)
2. **Select Model** (Nebius, OpenRouter, or Gemini)
3. **Choose Schema** (Invoice, Receipt, ID Card, Generic, or custom)
4. **Process** and view extracted structured data
5. **Review History** of all processing jobs

### Example: Processing an Invoice

1. Navigate to http://localhost:8000
2. Upload invoice image/PDF
3. Select provider: **Gemini**
4. Select model: **gemini-1.5-flash**
5. Select schema: **Invoice**
6. Click **Process Document**
7. View extracted data:
   ```json
   {
     "invoice_number": "INV-2024-001",
     "vendor_name": "Acme Corp",
     "total_amount": 150.00,
     "line_items": [...]
   }
   ```

## 🧪 Testing

📖 **For comprehensive testing procedures, see [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)**

### Running Tests

```bash
# Install test dependencies
cd backend
pip install -r requirements-test.txt

# Run unit tests
pytest tests/

# Run with coverage report
pytest --cov=services --cov-report=html

# Run integration tests (requires running backend)
pytest tests/test_integration.py
```

### Manual Testing Checklist

- [ ] Application starts without errors
- [ ] Health check returns success
- [ ] File upload works (JPG, PNG, PDF)
- [ ] Can select providers and models
- [ ] Can select built-in schemas
- [ ] Can create custom schemas
- [ ] Processing completes successfully
- [ ] Results display correctly
- [ ] History shows past jobs
- [ ] Can filter and delete jobs

## ❓ Troubleshooting

📖 **For detailed troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**

### Common Issues

**Port 8000 already in use**:
```bash
# Find and kill process
lsof -i :8000
kill -9 <PID>
```

**Docker won't start**:
```bash
# Check Docker is running
docker info

# Rebuild without cache
docker compose build --no-cache
docker compose up
```

**API key errors**:
- Verify `.env` file exists
- Check API keys are correct (no extra quotes or spaces)
- Ensure at least one provider key is configured

**Database errors**:
```bash
# Reinitialize database
cd backend
python -m database.migrations
```

## 📖 Additional Documentation

| Document | Description |
|----------|-------------|
| **[Setup Guide](docs/SETUP_GUIDE.md)** | Detailed setup instructions for Docker and local development |
| **[User Guide](docs/USER_GUIDE.md)** | Complete usage guide with examples and best practices |
| **[Testing Guide](docs/TESTING_GUIDE.md)** | Manual and automated testing procedures |
| **[Troubleshooting](docs/TROUBLESHOOTING.md)** | Common issues and solutions |
| **[Schema Guide](SCHEMA_GUIDE.md)** | Creating custom JSON schemas |
| **[Implementation Report](docs/IMPLEMENTATION_COMPLETE.md)** | Technical implementation details |
| **[Testing & Documentation Summary](docs/TESTING_AND_DOCUMENTATION_SUMMARY.md)** | Overview of all documentation and tests |

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

- `POST /api/upload` - Upload document
- `POST /api/process` - Process document with VLM
- `GET /api/process/status/{job_id}` - Get job status
- `GET /api/schemas` - List schemas
- `POST /api/schemas` - Create custom schema
- `GET /api/schemas/templates` - Get built-in templates
- `GET /api/jobs` - List processing jobs
- `GET /api/providers` - List available VLM providers

## Project Structure

```
ocr_platform_testdrive/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings management
│   ├── requirements.txt        # Python dependencies
│   ├── routers/                # API endpoints
│   │   ├── upload.py
│   │   ├── processing.py
│   │   ├── schemas.py
│   │   ├── jobs.py
│   │   └── providers.py
│   ├── services/               # Business logic
│   │   ├── vlm_provider.py     # Base provider class
│   │   ├── nebius.py           # Nebius provider
│   │   ├── openrouter.py       # OpenRouter provider
│   │   ├── gemini.py           # Gemini provider
│   │   ├── image_service.py    # Image processing
│   │   ├── schema_service.py   # Schema validation
│   │   └── processing.py       # Main pipeline
│   ├── database/               # Database layer
│   │   ├── schema.sql          # Database schema
│   │   ├── migrations.py       # DB initialization
│   │   └── crud.py             # CRUD operations
│   └── models/                 # Pydantic models
│       └── schemas.py
├── frontend/
│   ├── src/
│   │   ├── main.tsx            # React entry point
│   │   ├── App.tsx             # Main app with navigation
│   │   ├── lib/
│   │   │   └── api.ts          # API client
│   │   ├── components/         # React components
│   │   │   ├── FileUpload.tsx
│   │   │   ├── ModelSelector.tsx
│   │   │   ├── SchemaEditor.tsx
│   │   │   └── ResultsDisplay.tsx
│   │   └── pages/              # Page components
│   │       ├── ProcessingPage.tsx
│   │       └── HistoryPage.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml
└── .env.example                # Environment template
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEBIUS_API_KEY` | Nebius API key | No |
| `OPENROUTER_API_KEY` | OpenRouter API key | No |
| `GEMINI_API_KEY` | Google Gemini API key | No |
| `DATABASE_URL` | SQLite database path | No (default: ./data/ocr.db) |
| `MAX_UPLOAD_SIZE` | Max file size in bytes | No (default: 10485760) |

**Note**: At least one provider API key is required.

## Schema Guide

See [SCHEMA_GUIDE.md](./SCHEMA_GUIDE.md) for detailed information on creating custom JSON schemas for structured data extraction.

## Troubleshooting

### Docker Build Issues

- Ensure Docker daemon is running: `docker info`
- Rebuild without cache: `docker-compose build --no-cache`
- Check logs: `docker-compose logs -f`

### Database Issues

- Reinitialize database: `rm -rf data/ && docker-compose up`
- Check database permissions in `data/` directory

### VLM Provider Errors

- Verify API keys in `.env`
- Check provider service status
- Review rate limits and quotas

## License

MIT License - feel free to use this project for learning and development.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.
