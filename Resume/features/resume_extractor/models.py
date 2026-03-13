from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ParsedResume:
    text: str
    links: List[str]
    is_scanned_pdf: Optional[bool] = None
    classified_links: Optional[Dict] = None

    # populated later (LLM / enrichment phase)
    experiences: Optional[List[Dict]] = None
    internships: Optional[List[Dict]] = None
