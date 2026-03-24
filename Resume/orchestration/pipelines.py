import os
from pathlib import Path
from typing import Any

from Resume.core.config import LLMConfig
from Resume.core.interfaces import LLMClient
from Resume.features.chatbot.sanitizer import InputSanitizer
from Resume.features.chatbot.service import ResumeChatbotService
from Resume.features.chatbot.state_store.base import StateStore
from Resume.features.chatbot.state_store.memory_store import MemoryStateStore
from Resume.features.resume_extractor.exceptions import ResumeExtractionError
from Resume.features.resume_extractor.service import ResumeExtractionService
from Resume.features.video_validator.service import VideoValidationService


class ResumeOnboardingPipeline:
    """
    Pipeline until completed resume JSON is ready:
    upload -> extraction/guardrails -> missing fields -> chatbot completion.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        state_store: StateStore | None = None,
        extractor: ResumeExtractionService | None = None,
    ):
        self.extractor = extractor or ResumeExtractionService()
        self.chatbot = ResumeChatbotService(
            store=state_store or MemoryStateStore(),
            llm=llm_client,
            sanitizer=InputSanitizer(),
        )
        self.video_validator = VideoValidationService()
        self._post_chat_sessions: dict[str, dict[str, Any]] = {}

    async def start(self, user_id: str, file_path: str, file_type: str = "pdf") -> dict[str, Any]:
        try:
            extracted = await self.extractor.extract_full(file_path=file_path, file_type=file_type)
        except ResumeExtractionError as e:
            return {
                "status": "declined",
                "message": "Resume validation failed. Please re-upload a valid PDF.",
                "reason": str(e),
            }

        resume_json = extracted["resume_json"]
        missing_fields = extracted["missing_fields"]

        state = self.chatbot.start_or_resume(
            user_id=user_id,
            resume_json=resume_json,
            missing_fields=missing_fields,
        )

        if not state.pending_fields:
            self.chatbot.store.delete(user_id)
            self._post_chat_sessions[user_id] = {
                "resume_json": state.resume.data,
                "video_mode": None,
            }
            return {
                "status": "awaiting_video_choice",
                "message": "Choose AI video generation or upload your own video.",
                "video_options": ["ai_video_generation", "upload_video"],
                "resume_json": state.resume.data,
            }

        question = await self.chatbot.next_question(state)
        return {
            "status": "awaiting_answer",
            "question": question,
            "current_field": state.current_field,
            "missing_fields": list(state.pending_fields),
            "resume_json": state.resume.data,
        }

    async def submit_answer(self, user_id: str, answer: str) -> dict[str, Any]:
        state = self.chatbot.store.get(user_id)
        if not state:
            return {
                "status": "error",
                "message": "No active onboarding session for this user.",
            }

        result = await self.chatbot.handle_user_input(state, answer)

        if result.get("status") == "invalid":
            return {
                "status": "awaiting_answer",
                "question": result["question"],
                "current_field": state.current_field,
                "missing_fields": list(state.pending_fields),
            }

        if result.get("status") == "error":
            return {
                "status": "error",
                "message": result.get("message") or "Invalid request.",
            }

        if result.get("status") == "completed":
            self.chatbot.store.delete(user_id)
            self._post_chat_sessions[user_id] = {
                "resume_json": result["resume"],
                "video_mode": None,
            }
            return {
                "status": "awaiting_video_choice",
                "message": "Choose AI video generation or upload your own video.",
                "video_options": ["ai_video_generation", "upload_video"],
                "resume_json": result["resume"],
            }

        question = await self.chatbot.next_question(state)
        return {
            "status": "awaiting_answer",
            "question": question,
            "current_field": state.current_field,
            "missing_fields": list(state.pending_fields),
        }

    async def choose_video_option(
        self,
        user_id: str,
        option: str,
        output_dir: str | None = None,
        voice_id: str = "female",
    ) -> dict[str, Any]:
        session = self._post_chat_sessions.get(user_id)
        if not session:
            return {
                "status": "error",
                "message": "No completed chatbot session found. Finish resume onboarding first.",
            }

        normalized = (option or "").strip().lower()
        if normalized not in {"ai_video_generation", "upload_video"}:
            return {
                "status": "error",
                "message": "Invalid option. Use 'ai_video_generation' or 'upload_video'.",
            }

        session["video_mode"] = normalized
        resume_json = session["resume_json"]

        if normalized == "upload_video":
            return {
                "status": "awaiting_video_upload",
                "message": "Upload your video for validation.",
                "resume_json": resume_json,
            }

        return await self._generate_ai_video(
            user_id=user_id,
            resume_json=resume_json,
            output_dir=output_dir,
            voice_id=voice_id,
        )

    async def submit_uploaded_video(self, user_id: str, video_path: str) -> dict[str, Any]:
        session = self._post_chat_sessions.get(user_id)
        if not session:
            return {
                "status": "error",
                "message": "No active video-upload session found.",
            }

        if session.get("video_mode") != "upload_video":
            return {
                "status": "error",
                "message": "Video mode is not set to upload_video.",
            }

        resume_json = session["resume_json"]
        result = await self.video_validator.validate_video_async(video_path, resume_json)

        if not result.get("final_valid"):
            return {
                "status": "rejected_video",
                "message": "Uploaded video is not valid. Please reupload a proper video.",
                "reasons": self._collect_video_reasons(result),
                "validation_result": result,
            }

        final_resume = result.get("resume_json", resume_json)
        self._post_chat_sessions.pop(user_id, None)
        return {
            "status": "completed",
            "message": "Video validated and summary stored in resume_json.video_summary.",
            "resume_json": final_resume,
        }

    async def _generate_ai_video(
        self,
        user_id: str,
        resume_json: dict[str, Any],
        output_dir: str | None,
        voice_id: str,
    ) -> dict[str, Any]:
        try:
            from Resume.features.ai_video_generation.config import DEFAULT_LLM_MODEL
            from Resume.features.ai_video_generation.audio.tts_engine import TTSEngine
            from Resume.features.ai_video_generation.llm.script_generator import IntroScriptGenerator
            from Resume.features.ai_video_generation.service import AIVideoGenerationService
            from Resume.features.ai_video_generation.subtitles.srt_generator import SRTGenerator
            from Resume.features.ai_video_generation.video.renderer import VideoRenderer
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI video dependencies are not available: {e}",
            }

        api_key = LLMConfig.GROQ_API_KEY or os.getenv("AI_VIDEO_LLM_API_KEY")
        if not api_key:
            return {
                "status": "error",
                "message": "Missing API key for AI video generation (set GROQ_API_KEY).",
            }

        provider = (os.getenv("AI_VIDEO_LLM_PROVIDER") or "groq").strip().lower()
        model = (os.getenv("AI_VIDEO_LLM_MODEL") or DEFAULT_LLM_MODEL).strip()
        base_url = os.getenv("AI_VIDEO_LLM_API_BASE")

        target_dir = output_dir or str(Path("tmp") / "ai_video" / user_id)
        os.makedirs(target_dir, exist_ok=True)

        script_generator = IntroScriptGenerator(
            api_base=base_url,
            api_key=api_key,
            model=model,
            provider=provider,
        )
        tts_engine = TTSEngine(speaker=voice_id)
        srt_generator = SRTGenerator()
        video_renderer = VideoRenderer()
        ai_service = AIVideoGenerationService(
            script_generator=script_generator,
            tts_engine=tts_engine,
            srt_generator=srt_generator,
            video_renderer=video_renderer,
        )

        try:
            script = await ai_service.agenerate_script(resume_json)
            audio = tts_engine.synthesize(
                text=script,
                output_dir=target_dir,
                filename="intro_audio.wav",
                voice_id=voice_id,
            )
            srt_path = str(Path(target_dir) / "intro_subtitles.srt")
            video_path = str(Path(target_dir) / "intro_video.mp4")
            ai_service.finalize_video(script, audio.path, srt_path, video_path)
        except Exception as e:
            return {
                "status": "error",
                "message": f"AI video generation failed: {e}",
            }

        updated_resume = dict(resume_json)
        updated_resume["video_summary"] = script
        self._post_chat_sessions.pop(user_id, None)
        return {
            "status": "completed",
            "message": "AI video generated successfully.",
            "resume_json": updated_resume,
            "artifacts": {
                "audio_wav": audio.path,
                "subtitles_srt": srt_path,
                "video_mp4": video_path,
            },
        }

    @staticmethod
    def _collect_video_reasons(validation_result: dict[str, Any]) -> list[str]:
        reasons: list[str] = []
        for stage in ("video", "audio", "semantic", "moderation", "video_extraction"):
            payload = validation_result.get(stage) or {}
            stage_reasons = payload.get("reasons") or []
            for reason in stage_reasons:
                reasons.append(f"{stage}: {reason}")

        errors = validation_result.get("errors") or []
        for err in errors:
            reasons.append(f"{err.get('stage', 'unknown')}: {err.get('error', 'unknown error')}")

        # Stable dedupe preserving order.
        return list(dict.fromkeys(reasons))
