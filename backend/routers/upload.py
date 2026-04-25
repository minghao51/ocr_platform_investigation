from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pathlib import Path
from config import get_settings
from database import crud
from dependencies import get_optional_user
from limiter import limiter, get_rate_limit_value
from routers.shared import ensure_file_access
import uuid
import secrets
from paths import UPLOAD_DIR

router = APIRouter(prefix="/api/upload", tags=["upload"])
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".html"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS | AUDIO_EXTENSIONS


@router.post("/")
@limiter.limit(get_rate_limit_value)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict | None = Depends(get_optional_user),
):
    """Upload a file for processing"""
    settings = get_settings()
    guest_token = request.headers.get("X-Guest-Token")
    if current_user is None:
        guest_token = guest_token or secrets.token_urlsafe(32)

    content = await file.read()
    if len(content) > settings.max_file_size:
        max_size_mb = settings.max_file_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size is {max_size_mb:.0f}MB",
        )

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            ),
        )

    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine file type and content type
    if file_ext in IMAGE_EXTENSIONS:
        file_type = "image"
    elif file_ext == ".pdf":
        file_type = "pdf"
    elif file_ext in AUDIO_EXTENSIONS:
        file_type = "audio"
    else:
        file_type = "document"
    content_type_map = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".html": "text/html",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
    }
    content_type = content_type_map.get(file_ext, "application/octet-stream")

    # Store file metadata in database
    await crud.create_uploaded_file(
        file_id=file_id,
        original_filename=file.filename,
        file_extension=file_ext,
        file_path=str(file_path),
        file_size=len(content),
        content_type=content_type,
        user_id=current_user.get("user_id") if current_user else None,
        guest_token=guest_token,
    )

    payload = {
        "file_id": file_id,
        "file_name": file.filename,
        "file_type": file_type,
        "file_size": len(content),
    }
    if current_user is None:
        payload["guest_token"] = guest_token

    return JSONResponse(payload)


@router.post("/analyze-pdf/{file_id}")
async def analyze_pdf(
    file_id: str,
    request: Request,
    current_user: dict | None = Depends(get_optional_user),
):
    """Quick PDF text-layer detection for frontend method auto-selection."""
    file_record = await crud.get_uploaded_file(file_id)
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    ensure_file_access(file_record, current_user, request.headers.get("X-Guest-Token"))

    file_path = Path(file_record["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File has been deleted or moved")

    file_ext = (file_record["file_extension"] or "").lower()
    if file_ext != ".pdf":
        raise HTTPException(status_code=400, detail="File is not a PDF")

    try:
        import fitz

        doc = fitz.open(str(file_path))
        total_chars = 0
        for page in doc:
            total_chars += len(page.get_text("text").strip())
        doc.close()

        has_text = total_chars > 50
        return {
            "file_id": file_id,
            "has_text_layer": has_text,
            "text_chars": total_chars,
            "suggested_methods": (
                ["text", "vision", "hybrid", "docling-parse", "docling-extract", "transcription"]
                if has_text
                else ["vision", "hybrid", "docling-parse", "docling-extract", "transcription"]
            ),
        }
    except ImportError:
        raise HTTPException(status_code=500, detail="PDF analysis not available")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF analysis failed: {str(e)}")
