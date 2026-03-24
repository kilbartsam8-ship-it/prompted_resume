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
from Resume.features.resume_extractor.exceptions import (
    ResumeExtractionError,
    ResumeInputError,
    ResumeParseError,
    ResumeLLMOutputError,
    ResumeSecurityError,
)
from Resume.delivery.api.response_utils import (
    error_response,
    register_exception_handlers,
    success_response,
)


app = FastAPI(title="Resume Extraction API")
register_exception_handlers(app)
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


def _status_code_for_error(exc: Exception) -> int:
    if isinstance(exc, ResumeInputError):
        return 400
    if isinstance(exc, ResumeParseError):
        return 422
    if isinstance(exc, ResumeSecurityError):
        return 400
    if isinstance(exc, ResumeLLMOutputError):
        return 502
    return 500


@app.get("/health")
async def health() -> dict:
    return success_response("Health check successful.", 200, {"status": "ok"})


@app.post("/resume/extract/path")
async def resume_extract_by_path(body: ResumeExtractBody):
    try:
        result = await service.extract_full(body.file_path, body.file_type)
    except HTTPException as exc:
        return error_response(str(exc.detail), exc.status_code, {"user_id": body.user_id})
    except ResumeExtractionError as exc:
        return error_response(
            str(exc),
            _status_code_for_error(exc),
            {"user_id": body.user_id},
        )
    except Exception as exc:
        return error_response(
            str(exc) or "Unexpected error occurred.",
            500,
            {"user_id": body.user_id},
        )

    data = {"user_id": body.user_id, "result": result}
    return success_response(
        "Resume extraction completed successfully.",
        200,
        data,
    )


@app.post("/resume/extract/file")
async def resume_extract_by_file(
    user_id: str = Form(...),
    file: UploadFile = File(...),
    file_type: str | None = Form(None),
):
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400, detail="Uploaded file must have a filename."
            )

        saved = _save_upload(file, UPLOAD_DIR)
        resolved_file_type = (
            file_type or saved.suffix.replace(".", "") or "pdf"
        ).lower()
        result = await service.extract_full(str(saved), resolved_file_type)
    except HTTPException as exc:
        return error_response(str(exc.detail), exc.status_code, {"user_id": user_id})
    except ResumeExtractionError as exc:
        return error_response(
            str(exc),
            _status_code_for_error(exc),
            {"user_id": user_id},
        )
    except Exception as exc:
        return error_response(
            str(exc) or "Unexpected error occurred.",
            500,
            {"user_id": user_id},
        )

    data = {"user_id": user_id, "result": result}
    return success_response(
        "Resume extraction completed successfully.",
        200,
        data,
    )

# if __name__ == "__main__":
#     uvicorn.run("resume_extraction_api:app", host="0.0.0.0", port=5000, reload=True)
