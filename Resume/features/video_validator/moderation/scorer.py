# features/moderation/scorer.py

class ModerationScorer:
    def score(self, violations: int) -> str:
        if violations >= 3:
            return "high"
        elif violations == 2:
            return "medium"
        elif violations == 1:
            return "low"
        return "none"
