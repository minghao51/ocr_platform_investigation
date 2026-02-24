# Dependencies

## Backend (Python)
- **FastAPI**: Web framework
- **Pydantic v2**: Data validation
- **SQLAlchemy**: ORM
- **python-jose**: JWT handling
- **passlib**: Password hashing
- **pdfplumber**: PDF text extraction
- **slowapi**: Rate limiting
- **python-multipart**: File uploads

## Frontend (Node)
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **TailwindCSS**: Styling

## Environment Variables (`.env`)
```
NEBIUS_API_KEY=<key>
OPENROUTER_API_KEY=<key>
GEMINI_API_KEY=<key>
DATABASE_URL=sqlite:///./data/ocr_platform.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
JWT_SECRET_KEY=<secret>
```

## Database Schema
- **users**: id, username, hashed_password, is_admin, created_at
- **jobs**: id, user_id, filename, status, method, provider, model, schema, result, error, created_at, updated_at
- **schemas**: id, user_id, name, schema_json, is_builtin, created_at
