import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from Resume.features.ai_video_generation.exception import TTSError


@dataclass(frozen=True)
class VoiceProfile:
    id: str
    description: str
    prompt_env_var: Optional[str] = None

    @property
    def prompt_audio_path(self) -> Optional[str]:
        if not self.prompt_env_var:
            return None
        value = (os.getenv(self.prompt_env_var) or "").strip()
        return value or None


class VoiceRegistry:
    """
    Central registry for available voices.
    """

    VOICES: Dict[str, VoiceProfile] = {
        "male": VoiceProfile(
            id="male",
            description="Male voice from prompt audio",
            prompt_env_var="AI_VIDEO_TTS_MALE_PROMPT",
        ),
        "female": VoiceProfile(
            id="female",
            description="Female voice from prompt audio",
            prompt_env_var="AI_VIDEO_TTS_FEMALE_PROMPT",
        ),
    }
    ALIASES: Dict[str, str] = {
        "male_neutral": "male",
        "female_warm": "female",
        "female_confident": "female",
        "p226": "male",
        "p225": "female",
    }

    @classmethod
    def list_voices(cls) -> List[VoiceProfile]:
        return list(cls.VOICES.values())

    @classmethod
    def get(cls, voice_id: str) -> VoiceProfile:
        if not voice_id or not isinstance(voice_id, str):
            raise TTSError("voice_id must be a non-empty string.")

        resolved = cls.ALIASES.get(voice_id, voice_id)
        if resolved not in cls.VOICES:
            supported = ", ".join(sorted(cls.VOICES.keys()))
            raise TTSError(f"Unsupported voice_id '{voice_id}'. Supported voices: {supported}")
        return cls.VOICES[resolved]
