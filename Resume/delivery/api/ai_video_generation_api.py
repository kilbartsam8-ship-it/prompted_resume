import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
import uvicorn
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Resume.features.ai_video_generation.config import DEFAULT_LLM_MODEL, DEFAULT_TTS_MODEL
from Resume.features.ai_video_generation.exception import AIVideoError
from Resume.features.ai_video_generation.service import AIVideoGenerationService
from Resume.features.ai_video_generation.audio.tts_engine import TTSEngine
from Resume.features.ai_video_generation.llm.script_generator import IntroScriptGenerator
from Resume.features.ai_video_generation.subtitles.srt_generator import SRTGenerator
from Resume.features.ai_video_generation.video.renderer import VideoRenderer


app = FastAPI(title="AI Video Generation API")


class AIVideoGenerateBody(BaseModel):
    user_id: str = Field(..., description="User identifier")
    resume_json: dict = Field(..., description="Resume JSON object")
    voice_id: str | None = Field(None, description="Voice id: male or female")
    audio_path: str | None = Field(
        None,
        description="Optional custom audio file path. If provided, TTS generation is skipped.",
    )


class AIVideoGeneratePathBody(BaseModel):
    user_id: str = Field(..., description="User identifier")
    resume_json_path: str = Field(..., description="Path to resume JSON file")
    voice_id: str | None = Field(None, description="Voice id: male or female")
    audio_path: str | None = Field(
        None,
        description="Optional custom audio file path. If provided, TTS generation is skipped.",
    )


TMP_DIR = PROJECT_ROOT / "tmp" / "ai_video_generation_api"
UPLOAD_DIR = TMP_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _save_upload(upload: UploadFile, target_dir: Path) -> Path:
    name = (upload.filename or "upload.bin").replace("/", "_").replace("\\", "_")
    target = target_dir / f"{uuid.uuid4().hex}_{name}"
    with target.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return target


def _load_resume_json_from_upload(upload: UploadFile) -> dict:
    raw = upload.file.read()
    upload.file.seek(0)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid resume JSON file: {exc}") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="resume_json file must contain a JSON object.")

    return payload


def _load_resume_json_from_path(resume_json_path: str) -> dict:
    path = Path(resume_json_path)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=400, detail=f"resume_json_path not found: {resume_json_path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid resume JSON file: {exc}") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="resume_json file must contain a JSON object.")

    return payload


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


async def _generate_ai_video(
    user_id: str,
    resume_json: dict,
    voice_id_input: str | None = None,
    audio_path_input: str | None = None,
):

    output_dir = str(PROJECT_ROOT / "tmp" / "ai_video_output" / user_id)
    os.makedirs(output_dir, exist_ok=True)

    api_base = os.getenv("AI_VIDEO_LLM_API_BASE") or os.getenv("GROQ_API_BASE")
    api_key = os.getenv("AI_VIDEO_LLM_API_KEY") or os.getenv("GROQ_API_KEY")
    llm_model = os.getenv("AI_VIDEO_LLM_MODEL") or DEFAULT_LLM_MODEL
    provider = (os.getenv("AI_VIDEO_LLM_PROVIDER") or "groq").strip().lower()
    if isinstance(llm_model, str) and llm_model.strip().lower() in {"string", "str", ""}:
        llm_model = DEFAULT_LLM_MODEL

    tts_model = os.getenv("AI_VIDEO_TTS_MODEL") or DEFAULT_TTS_MODEL
    voice_id = (voice_id_input or os.getenv("AI_VIDEO_TTS_VOICE") or "female").lower()
    use_gpu = (os.getenv("AI_VIDEO_TTS_GPU") or "false").strip().lower() in {"1", "true", "yes"}

    if not api_key:
        raise HTTPException(status_code=400, detail="api_key is required.")

    script_generator = IntroScriptGenerator(
        api_base=api_base,
        api_key=api_key,
        model=llm_model,
        provider=provider,
    )
    tts_engine = TTSEngine(model_name=tts_model, gpu=use_gpu, speaker=voice_id)
    srt_generator = SRTGenerator()
    video_renderer = VideoRenderer()
    ai_service = AIVideoGenerationService(
        script_generator=script_generator,
        tts_engine=tts_engine,
        srt_generator=srt_generator,
        video_renderer=video_renderer,
    )

    script_path = os.path.join(output_dir, "intro_script.txt")
    srt_path = os.path.join(output_dir, "intro_subtitles.srt")
    video_path = os.path.join(output_dir, "intro_video.mp4")
    manifest_path = os.path.join(output_dir, "generation_result.json")

    try:
        script = await ai_service.agenerate_script(resume_json)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        used_custom_audio = False
        if audio_path_input:
            source_audio = Path(audio_path_input)
            if not source_audio.exists() or not source_audio.is_file():
                raise HTTPException(status_code=400, detail=f"audio_path not found: {audio_path_input}")
            audio_path = str(source_audio)
            used_custom_audio = True
        else:
            audio_artifact = tts_engine.synthesize(
                text=script,
                output_dir=output_dir,
                filename="intro_audio.wav",
                voice_id=voice_id,
            )
            audio_path = audio_artifact.path

        ai_service.finalize_video(script, audio_path, srt_path, video_path)
    except AIVideoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI video generation failed: {exc}") from exc

    result = {
        "user_id": user_id,
        "intro_script": script,
        "audio_source": "custom" if used_custom_audio else "default_tts",
        "artifacts": {
            "script_txt": script_path,
            "audio_wav": audio_path,
            "subtitles_srt": srt_path,
            "video_mp4": video_path,
        },
        "config": {
            "llm_model": llm_model,
            "provider": provider,
            "tts_model_requested": tts_model,
            "tts_model_loaded": tts_engine.model_name,
            "tts_voice_choice": voice_id,
            "gpu": use_gpu,
        },
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result

@app.post("/ai-video/generate/path")
async def ai_video_generate_by_path(body: AIVideoGeneratePathBody):
    resume_json = _load_resume_json_from_path(body.resume_json_path)
    return await _generate_ai_video(
        user_id=body.user_id,
        resume_json=resume_json,
        voice_id_input=body.voice_id,
        audio_path_input=body.audio_path,
    )


@app.post("/ai-video/generate/file")
async def ai_video_generate_by_file(
    user_id: str = Form(...),
    resume_json_file: str = Form(..., description="Resume JSON file upload"),
    voice_id: str | None = Form(None),
    audio_file: UploadFile | None = File(None, description="Optional custom audio file"),
):
    resume_json = _load_resume_json_from_upload(resume_json_file)

    audio_path: str | None = None
    if audio_file is not None:
        saved_audio = _save_upload(audio_file, UPLOAD_DIR)
        audio_path = str(saved_audio)

    return await _generate_ai_video(
        user_id=user_id,
        resume_json=resume_json,
        voice_id_input=voice_id,
        audio_path_input=audio_path,
    )

# if __name__ == "__main__":
#     uvicorn.run("ai_video_generation_api:app", host="0.0.0.0", port=8080, reload=True)