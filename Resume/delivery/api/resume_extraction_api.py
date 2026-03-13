import shutil
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Resume.features.resume_extractor.service import ResumeExtractionService


app = FastAPI(title="Resume Extraction API")
service = ResumeExtractionService()

TMP_DIR = PROJECT_ROOT / "tmp" / "resume_extraction_api"
UPLOAD_DIR = TMP_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class ResumeExtractBody(BaseModel):
    user_id: str = Field(..., description="User identifier")
    file_path: str = Field(..., description="Absolute or relative resume file path")
    file_type: str = Field("pdf", description="pdf | docx | txt")


def _save_upload(upload: UploadFile, target_dir: Path) -> Path:
    name = (upload.filename or "upload.bin").replace("/", "_").replace("\\", "_")
    target = target_dir / f"{uuid.uuid4().hex}_{name}"
    with target.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return target


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/resume/extract/path")
async def resume_extract_by_path(body: ResumeExtractBody):
    return await service.extract_full(body.file_path, body.file_type)


@app.post("/resume/extract/file")
async def resume_extract_by_file(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    file_type: str | None = Form(None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename.")

    saved = _save_upload(file, UPLOAD_DIR)
    resolved_file_type = (file_type or saved.suffix.replace(".", "") or "pdf").lower()
    return await service.extract_full(str(saved), resolved_file_type)

# if __name__ == "__main__":
#     uvicorn.run("resume_extraction_api:app", host="0.0.0.0", port=5000, reload=True)