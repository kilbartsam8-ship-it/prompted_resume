import os
from typing import List
from Resume.features.ai_video_generation.audio.tts_engine import TTSEngine
from Resume.features.ai_video_generation.audio.audio_models import AudioArtifact
from Resume.features.ai_video_generation.audio.voice_registry import VoiceRegistry
from Resume.features.ai_video_generation.exception import AIVideoError


class VoicePreviewService:
    """
    Generates preview audios for multiple voices.
    """

    def generate_previews(
        self,
        script: str,
        output_dir: str,
        voice_ids: List[str],
        gpu: bool = False,
    ) -> List[AudioArtifact]:
        if not isinstance(script, str) or not script.strip():
            raise AIVideoError("script cannot be empty.")
        if not isinstance(output_dir, str) or not output_dir.strip():
            raise AIVideoError("output_dir must be a non-empty string.")
        if not isinstance(voice_ids, list) or not voice_ids:
            raise AIVideoError("voice_ids must be a non-empty list.")

        os.makedirs(output_dir, exist_ok=True)

        previews = []
        engine = TTSEngine(gpu=gpu)

        for voice_id in voice_ids:
            voice = VoiceRegistry.get(voice_id)

            audio = engine.synthesize(
                text=script,
                output_dir=output_dir,
                filename=f"preview_{voice.id}.wav",
                voice_id=voice.id,
            )

            previews.append(
                AudioArtifact(
                    path=audio.path,
                    duration_seconds=audio.duration_seconds,
                    sample_rate=audio.sample_rate,
                    language="en",
                    voice_id=voice.id,
                )
            )

        return previews
