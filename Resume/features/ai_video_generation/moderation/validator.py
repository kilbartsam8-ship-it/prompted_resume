from Resume.features.ai_video_generation.moderation.models import ModerationResult
from Resume.features.ai_video_generation.exception import ModerationRejectedError


class AudioModerationValidator:
    def validate(self, result: ModerationResult):
        if not result.is_allowed:
            raise ModerationRejectedError(
                f"Audio content rejected. Severity={result.severity}"
            )
