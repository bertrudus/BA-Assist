"""Upload router — file upload handling."""

from fastapi import APIRouter, UploadFile

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload")
async def upload_file(file: UploadFile):
    """Read an uploaded file and return its text content."""
    content = await file.read()
    text = content.decode("utf-8")
    return {"filename": file.filename, "text": text, "size": len(text)}
