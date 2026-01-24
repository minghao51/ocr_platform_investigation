# OCR Platform

A modern OCR platform that uses Vision Language Models to extract structured data from documents. Supports multiple VLM providers (Nebius, OpenRouter, Google Gemini) with intelligent auto-routing between text and vision processing pipelines.

## Features

- Multi-provider VLM support (Nebius, OpenRouter, Gemini)
- Intelligent document auto-routing (text vs vision extraction)
- Schema-based structured data extraction
- Built-in templates (Invoice, Receipt, ID Card, Generic)
- Real-time background processing with job tracking
- React + TypeScript frontend

## Tech Stack

**Backend**: FastAPI + Python 3.11 + SQLite + Pydantic v2
**Frontend**: React 18 + TypeScript + Vite + TailwindCSS
**Infrastructure**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose (or Python 3.11+ and Node 18+)
- API keys for at least one VLM provider

### Setup

```bash
# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Run with Docker (recommended)
docker compose up --build

# Or run locally
cd backend && uv run uvicorn main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

Visit http://localhost:8000

## Usage

1. Upload document (JPEG, PNG, GIF, WebP, or PDF)
2. Select provider and model
3. Choose extraction schema (Invoice, Receipt, ID Card, Generic, or custom)
4. View extracted structured data
5. Review job history

For detailed usage instructions, see the [User Guide](docs/guides/user-guide.md)

## Documentation

| Document | Description |
|----------|-------------|
| [Setup Guide](docs/guides/setup.md) | Setup instructions for Docker and local development |
| [User Guide](docs/guides/user-guide.md) | Complete usage guide with examples |
| [Schema Guide](docs/guides/schema-guide.md) | Creating custom JSON schemas |
| [API Reference](docs/guides/api.md) | Complete API documentation |
| [Troubleshooting](docs/guides/troubleshooting.md) | Common issues and solutions |
| [Testing Guide](docs/development/testing-guide.md) | Testing procedures |
| [claude.md](claude.md) | Developer context and project overview |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEBIUS_API_KEY` | Nebius API key | No |
| `OPENROUTER_API_KEY` | OpenRouter API key | No |
| `GEMINI_API_KEY` | Google Gemini API key | No |
| `DATABASE_URL` | SQLite database path | No |
| `MAX_UPLOAD_SIZE` | Max file size in bytes | No |

**Note**: At least one provider API key is required.

## API Documentation

Interactive API docs available at http://localhost:8000/docs

For complete API reference, see [docs/guides/api.md](docs/guides/api.md)

## Project Structure

```
ocr_platform_testdrive/
├── backend/          # FastAPI application
│   ├── routers/      # API endpoints
│   ├── services/     # Business logic
│   ├── database/     # Database layer
│   └── models/       # Pydantic models
├── frontend/         # React application
│   └── src/
│       ├── components/  # UI components
│       └── pages/       # Page components
├── docs/             # Documentation
└── Dockerfile
```

For detailed project structure, see [docs/implementation/project-structure.md](docs/implementation/project-structure.md)

## License

MIT License - feel free to use this project for learning and development.

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.
