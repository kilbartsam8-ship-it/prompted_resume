from Resume.features.ai_video_generation.moderation.rules import find_matches
from Resume.features.ai_video_generation.moderation.models import ModerationResult


class AudioModerationDetector:
    """
    Rule-based moderation for generated speech.
    (LLM-based moderation can be plugged later)
    """

    def detect(self, transcript: str) -> ModerationResult:
        matches = find_matches(transcript)
        severity = min(1.0, len(matches) * 0.3)

        return ModerationResult(
            is_allowed=severity < 0.5,
            severity=severity,
            flagged_terms=matches,
        )
