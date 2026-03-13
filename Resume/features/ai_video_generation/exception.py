class AIVideoError(Exception):
    pass


class ScriptGenerationError(AIVideoError):
    pass


class TTSError(AIVideoError):
    pass


class SubtitleError(AIVideoError):
    pass


class VideoRenderError(AIVideoError):
    pass

class ModerationRejectedError(AIVideoError):
    pass