from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AudioArtifact:
    """
    Represents a generated audio file and its metadata.
    This is passed across modules instead of raw paths.
    """
    path: str
    duration_seconds: Optional[float] = None
    sample_rate: Optional[int] = None
    language: str = "en"
    voice_id: Optional[str] = None
