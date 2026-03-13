# features/video_validator/audio/validator.py

from Resume.features.video_validator.models import AudioAnalysisResult


class AudioValidator:
    def validate(
        self,
        transcript: str,
        duration_seconds: float,
        language: str | None
    ) -> AudioAnalysisResult:

        reasons = []

        if not transcript.strip():
            reasons.append("No speech detected")

        if duration_seconds < 5:
            reasons.append("Audio too short")

        return AudioAnalysisResult(
            transcript=transcript,
            duration_seconds=duration_seconds,
            language=language,
            is_valid=len(reasons) == 0,
            reasons=reasons,
        )
