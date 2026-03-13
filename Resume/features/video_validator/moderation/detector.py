# features/moderation/detector.py

import re
from typing import List

from Resume.features.video_validator.moderation.rules import (
    PROFANITY_WORDS,
    HATE_PATTERNS,
    SEXUAL_PATTERNS
)
from Resume.features.video_validator.moderation.models import ModerationResult
from Resume.features.video_validator.moderation.scorer import ModerationScorer
from Resume.features.video_validator.moderation.sanitizer import TextSanitizer


class ToxicityDetector:
    def __init__(self):
        self.scorer = ModerationScorer()
        self.sanitizer = TextSanitizer()

    def detect(self, text: str) -> ModerationResult:
        text = self.sanitizer.normalize(text)

        categories: List[str] = []
        reasons: List[str] = []
        violations = 0

        # profanity
        if any(word in text for word in PROFANITY_WORDS):
            violations += 1
            categories.append("profanity")
            reasons.append("Contains profanity")

        # hate
        if any(re.search(p, text) for p in HATE_PATTERNS):
            violations += 1
            categories.append("hate")
            reasons.append("Contains hate-related language")

        # sexual
        if any(re.search(p, text) for p in SEXUAL_PATTERNS):
            violations += 1
            categories.append("sexual")
            reasons.append("Contains sexual content")

        severity = self.scorer.score(violations)

        return ModerationResult(
            is_allowed=severity in ("none", "low"),
            severity=severity,
            categories=categories,
            reasons=reasons
        )
