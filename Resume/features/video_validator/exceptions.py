# features/video_validator/exceptions.py

class VideoValidationError(Exception):
    """Raised when video validation fails due to unreadable video or missing frames."""
    pass


class InputValidationError(Exception):
    """Raised when incoming validation inputs are invalid."""
    pass


class AudioExtractionError(Exception):
    """Raised when audio extraction fails."""
    pass

class TranscriptionError(Exception):
    """Raised when speech transcription fails."""
    pass

class SemanticMatchingError(Exception):
    """Raised when semantic comparison fails."""
    pass

class ModerationError(Exception):
    """Raised when moderation fails."""
    pass


class VideoExtractionError(Exception):
    """Raised when professional video summary extraction fails."""
    pass
