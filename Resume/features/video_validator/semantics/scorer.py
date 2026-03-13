# features/semantic_matching/scorer.py

from Resume.features.video_validator.semantics.config import (
    COSINE_MATCH_THRESHOLD,
    HIGH_CONFIDENCE_THRESHOLD
)
from Resume.features.video_validator.semantics.models import SemanticScore


class SemanticScorer:
    def score(self, similarity: float) -> SemanticScore:
        if similarity >= HIGH_CONFIDENCE_THRESHOLD:
            confidence = "high"
        elif similarity >= COSINE_MATCH_THRESHOLD:
            confidence = "medium"
        else:
            confidence = "low"

        return SemanticScore(
            similarity=similarity,
            confidence=confidence,
            is_match=similarity >= COSINE_MATCH_THRESHOLD
        )
