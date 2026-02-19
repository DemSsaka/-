from pathlib import Path
import secrets

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_current_user
from app.core.config import settings
from app.models.models import User

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIME = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}
MAX_SIZE = 5 * 1024 * 1024


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    ext = ALLOWED_MIME.get(file.content_type or "")
    if not ext:
        raise HTTPException(status_code=415, detail="Unsupported image type")

    data = await file.read()
    if not data or len(data) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Invalid file size")

    filename = f"{current_user.id}_{secrets.token_hex(8)}{ext}"
    out = UPLOAD_DIR / filename
    out.write_bytes(data)
    return {"url": f"{settings.api_origin}/uploads/{filename}"}
