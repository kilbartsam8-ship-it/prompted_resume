# features/semantic_matching/validator.py

from Resume.features.video_validator.semantics.models import (
    SemanticInput,
    SemanticMatchResult
)
from Resume.features.video_validator.semantics.scorer import SemanticScorer
from Resume.features.video_validator.semantics.matcher import SemanticMatcher


class SemanticValidator:
    def __init__(self, matcher: SemanticMatcher):
        self.matcher = matcher
        self.scorer = SemanticScorer()

    def validate(self, source: str, target: str) -> SemanticMatchResult:
        similarity = self.matcher.compare(source, target)
        score = self.scorer.score(similarity)

        reasons = []
        if not score.is_match:
            reasons.append("Semantic similarity below threshold")

        return SemanticMatchResult(
            input=SemanticInput(source, target),
            score=score,
            reasons=reasons
        )
