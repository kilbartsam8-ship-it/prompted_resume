import json
import shutil
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Resume.features.video_validator.service import VideoValidationService


app = FastAPI(title="Video Validation API")
service = VideoValidationService()

TMP_DIR = PROJECT_ROOT / "tmp" / "video_validation_api"
UPLOAD_DIR = TMP_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class VideoValidateBody(BaseModel):
    user_id: str = Field(..., description="User identifier")
    video_path: str = Field(..., description="Absolute or relative video file path")
    resume_json: dict | None = Field(None, description="Optional resume JSON object")


def _save_upload(upload: UploadFile, target_dir: Path) -> Path:
    name = (upload.filename or "upload.bin").replace("/", "_").replace("\\", "_")
    target = target_dir / f"{uuid.uuid4().hex}_{name}"
    with target.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return target


def _load_json_file(upload: UploadFile) -> dict:
    raw = upload.file.read()
    upload.file.seek(0)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {exc}") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="resume_json file must contain a JSON object.")

    return payload


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/video/validate/path")
async def validate_video_by_path(body: VideoValidateBody):
    result = await service.validate_video_async(body.video_path, body.resume_json or {})
    result["user_id"] = body.user_id
    return result


@app.post("/video/validate/file")
async def validate_video_by_file(
    user_id: str = Form(...),
    video: UploadFile = File(...),
    resume_json: str = Form(None, description="Optional resume JSON string")
):

    saved_video = _save_upload(video, UPLOAD_DIR)
    resume_data: dict = {}
    if resume_json is not None:
        resume_data = _load_json_file(resume_json)

    result = await service.validate_video_async(str(saved_video), resume_data)
    result["user_id"] = user_id
    return result

# if __name__ == "__main__":
#     uvicorn.run("video_validation_api:app", host="0.0.0.0", port=80, reload=True)