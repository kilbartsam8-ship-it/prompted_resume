# features/semantic_matching/models.py

from dataclasses import dataclass
from typing import List


@dataclass
class SemanticInput:
    source_text: str
    target_text: str


@dataclass
class SemanticScore:
    similarity: float
    confidence: str   # low / medium / high
    is_match: bool


@dataclass
class SemanticMatchResult:
    input: SemanticInput
    score: SemanticScore
    reasons: List[str]
