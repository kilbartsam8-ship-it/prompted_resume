# features/moderation/models.py

from dataclasses import dataclass
from typing import List


@dataclass
class ModerationResult:
    is_allowed: bool
    severity: str           # low | medium | high
    categories: List[str]   # abuse, hate, sexual, profanity
    reasons: List[str]
