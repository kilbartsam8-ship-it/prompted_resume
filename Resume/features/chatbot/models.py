from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class ResumeData:
    data: Dict[str, Any]

@dataclass
class ChatState:
    user_id: str
    resume: ResumeData
    pending_fields: List[str]
    current_field: str | None = None
    completed: bool = False
