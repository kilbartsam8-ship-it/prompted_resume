from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ModerationResult:
    is_allowed: bool
    severity: float
    flagged_terms: List[str]
