from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import uuid

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing"""

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max size is 10MB")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}{file_ext}"

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine file type
    file_type = "pdf" if file_ext == ".pdf" else "image"

    return JSONResponse({
        "file_id": file_id,
        "file_name": file.filename,
        "file_type": file_type,
        "file_path": str(file_path),
        "file_size": len(content)
    })
