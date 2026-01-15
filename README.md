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

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- API keys for at least one VLM provider

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

### Running with Docker

```bash
# Build and start the application
docker-compose up --build

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

## Usage

### 1. Upload Document

Navigate to the **Process** page and upload a document:
- Drag and drop or click to browse
- Supports images (JPEG, PNG, GIF, WebP) and PDFs
- Maximum file size: 10MB

### 2. Select Model

Choose your VLM provider and model:
- **Nebius**: Llama 3.2 11B Vision
- **OpenRouter**: Claude 3.5 Sonnet, GPT-4o, Gemini 1.5, Llama 3.2
- **Gemini**: Gemini 1.5 Pro, Gemini 1.5 Flash

### 3. Define Schema

Select a built-in template or create a custom JSON schema:

**Built-in Templates:**
- **Invoice**: Extract invoice number, date, vendor, line items, totals
- **Receipt**: Extract merchant, date, items, total, payment method
- **ID Card**: Extract document type, name, DOB, document number, address
- **Generic**: Extract raw text and entities

**Custom Schema Example:**
```json
{
  "type": "object",
  "properties": {
    "title": {"type": "string"},
    "author": {"type": "string"},
    "content": {"type": "string"}
  },
  "required": ["title", "content"]
}
```

### 4. Process and Review

Click **Process Document** to start extraction:
- Real-time status updates (pending → processing → success/error)
- View extracted structured data
- Copy JSON results
- Track processing time

### 5. History

View all past jobs on the **History** page:
- Filter by status and provider
- View detailed results
- Delete old jobs

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
