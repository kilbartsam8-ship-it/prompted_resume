# features/video_validator/models.py

from dataclasses import dataclass
from typing import List, Dict, Optional


# =====================
# Video
# =====================

@dataclass
class VideoAnalysisResult:
    total_frames: int
    frames_with_person: int
    multiple_person_frames: int
    frames_with_unwanted_objects: int
    unwanted_objects: List[str]
    center_deviation_score: float
    movement_score: float
    is_valid: bool
    reasons: List[str]


# =====================
# Audio / Transcript
# =====================

@dataclass
class AudioAnalysisResult:
    transcript: str
    duration_seconds: float
    language: Optional[str]
    is_valid: bool
    reasons: List[str]


# =====================
# Semantic Matching
# =====================

@dataclass
class SemanticMatchResult:
    overall_similarity: float
    entity_similarity: float
    matched_skills: List[str]
    missing_skills: List[str]
    is_valid: bool
    reasons: List[str]


# =====================
# Toxicity
# =====================

@dataclass
class ToxicityResult:
    toxic_sentence_count: int
    max_toxicity_score: float
    is_valid: bool
    reasons: List[str]


# =====================
# Final Verdict
# =====================

@dataclass
class ValidationResult:
    video: VideoAnalysisResult
    audio: AudioAnalysisResult
    semantics: SemanticMatchResult
    toxicity: ToxicityResult
    is_valid: bool
    reasons: List[str]
