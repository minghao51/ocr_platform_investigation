from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pathlib import Path
from config import get_settings
from database import crud
from dependencies import get_optional_user
from limiter import limiter, get_rate_limit_value
import uuid
import secrets
from paths import UPLOAD_DIR

router = APIRouter(prefix="/api/upload", tags=["upload"])
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt", ".md", ".html"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS


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
