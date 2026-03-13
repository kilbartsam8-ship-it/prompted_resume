# semantic_matching/models.py

from dataclasses import dataclass
from typing import List


@dataclass
class MatchingScore:
    cosine: float
    euclidean: float
    final_score: float


@dataclass
class JDMatchResult:
    jd_id: str
    title: str
    score: MatchingScore


@dataclass
class SemanticMatchResponse:
    resume_text: str
    matches: List[JDMatchResult]
