import os
from pathlib import Path
from typing import Iterable

from Resume.features.ai_video_generation.audio.audio_models import AudioArtifact
from Resume.features.ai_video_generation.moderation.detector import AudioModerationDetector
from Resume.features.ai_video_generation.moderation.validator import AudioModerationValidator
from Resume.features.ai_video_generation.audio.voice_registry import VoiceRegistry
from Resume.features.ai_video_generation.audio.voice_selector import VoicePreviewService
from Resume.features.ai_video_generation.exception import AIVideoError


class AIVideoGenerationService:
    MAX_SCRIPT_CHARS = 6000

    def __init__(
        self,
        script_generator,
        tts_engine,
        srt_generator,
        video_renderer
    ):
        self.script_generator = script_generator
        self.tts_engine = tts_engine
        self.srt_generator = srt_generator
        self.video_renderer = video_renderer
        self.voice_preview_service = VoicePreviewService()
        self.moderation_detector = AudioModerationDetector()
        self.moderation_validator = AudioModerationValidator()

    def generate_previews(self, script: str, output_dir: str, voices):
        script = self._validate_script(script)
        self._validate_output_dir(output_dir)
        voice_ids = self._normalize_voice_ids(voices)

        moderation = self.moderation_detector.detect(script)
        self.moderation_validator.validate(moderation)

        return self.voice_preview_service.generate_previews(
            script=script,
            output_dir=output_dir,
            voice_ids=voice_ids,
        )

    async def agenerate_script(self, resume_json: dict) -> str:
        self._validate_resume_json(resume_json)
        script = await self.script_generator.agenerate_text(resume_json)
        script = self._validate_script(script)

        moderation = self.moderation_detector.detect(script)
        self.moderation_validator.validate(moderation)
        return script

    async def agenerate_script_structured(self, resume_json: dict):
        self._validate_resume_json(resume_json)
        response = await self.script_generator.agenerate_structured(resume_json)
        response.script = self._validate_script(response.script)

        moderation = self.moderation_detector.detect(response.script)
        self.moderation_validator.validate(moderation)
        return response

    def finalize_video(
        self, script: str, audio_path: str, srt_path: str, video_path: str
    ):
        script = self._validate_script(script)
        audio_artifact = self._validate_audio_path(audio_path)
        srt_path = self._validate_output_file_path(srt_path, ".srt")
        video_path = self._validate_output_file_path(video_path, ".mp4")

        moderation = self.moderation_detector.detect(script)
        self.moderation_validator.validate(moderation)

        self.srt_generator.generate(audio_artifact, script, srt_path)
        self.video_renderer.render(audio_artifact.path, srt_path, video_path)

    def _validate_resume_json(self, resume_json: dict):
        if not isinstance(resume_json, dict):
            raise AIVideoError("resume_json must be a dictionary.")
        if not resume_json:
            raise AIVideoError("resume_json cannot be empty.")

    def _validate_script(self, script: str) -> str:
        if not isinstance(script, str):
            raise AIVideoError("script must be a string.")
        normalized = script.strip()
        if not normalized:
            raise AIVideoError("script cannot be empty.")
        if len(normalized) > self.MAX_SCRIPT_CHARS:
            raise AIVideoError(
                f"script is too long ({len(normalized)} chars). Maximum is {self.MAX_SCRIPT_CHARS}."
            )
        return normalized

    def _normalize_voice_ids(self, voices: Iterable[str]) -> list[str]:
        if voices is None:
            raise AIVideoError("voices must be provided.")

        if isinstance(voices, str):
            voices = [voices]

        voice_ids = [v for v in voices if isinstance(v, str) and v.strip()]
        if not voice_ids:
            raise AIVideoError("voices must contain at least one valid voice id.")

        resolved: list[str] = []
        for voice_id in voice_ids:
            resolved.append(VoiceRegistry.get(voice_id).id)

        # Keep order while deduplicating.
        return list(dict.fromkeys(resolved))

    @staticmethod
    def _validate_output_dir(output_dir: str):
        if not output_dir or not isinstance(output_dir, str):
            raise AIVideoError("output_dir must be a non-empty string.")
        os.makedirs(output_dir, exist_ok=True)

    @staticmethod
    def _validate_audio_path(audio_path: str) -> AudioArtifact:
        if not audio_path or not isinstance(audio_path, str):
            raise AIVideoError("audio_path must be a non-empty string.")
        path = Path(audio_path)
        if not path.exists():
            raise AIVideoError(f"Audio file not found: {audio_path}")
        return AudioArtifact(path=str(path))

    @staticmethod
    def _validate_output_file_path(path: str, required_suffix: str) -> str:
        if not path or not isinstance(path, str):
            raise AIVideoError("Output path must be a non-empty string.")
        target = Path(path)
        if target.suffix.lower() != required_suffix:
            raise AIVideoError(f"Output path must end with {required_suffix}: {path}")
        os.makedirs(target.parent, exist_ok=True)
        return str(target)
