# features/video_validator/video/validator.py

from typing import List, Tuple
from Resume.features.video_validator.config import (
    MIN_PERSON_FRAMES_RATIO,
    MAX_ALLOWED_PERSONS,
    MAX_CENTER_OFFSET_RATIO,
    MAX_MOVEMENT_STD,
)
from Resume.features.video_validator.models import VideoAnalysisResult


class VideoValidator:
    def validate(
        self,
        total_frames: int,
        frames_with_person: int,
        multiple_person_frames: int,
        unwanted_object_frames: int,
        unwanted_objects: List[str],
        center_score: float,
        movement_score: float,
    ) -> VideoAnalysisResult:

        reasons = []

        if frames_with_person / max(total_frames, 1) < MIN_PERSON_FRAMES_RATIO:
            reasons.append("Person not visible in enough frames")

        if multiple_person_frames > 0:
            reasons.append("Multiple people detected")

        if unwanted_object_frames > 0:
            labels = ", ".join(unwanted_objects) if unwanted_objects else "unwanted objects"
            reasons.append(f"Unwanted objects detected: {labels}")

        if center_score > MAX_CENTER_OFFSET_RATIO:
            reasons.append("Person not centered")

        if movement_score > MAX_MOVEMENT_STD:
            reasons.append("Too much movement")

        return VideoAnalysisResult(
            total_frames=total_frames,
            frames_with_person=frames_with_person,
            multiple_person_frames=multiple_person_frames,
            frames_with_unwanted_objects=unwanted_object_frames,
            unwanted_objects=unwanted_objects,
            center_deviation_score=center_score,
            movement_score=movement_score,
            is_valid=len(reasons) == 0,
            reasons=reasons,
        )
