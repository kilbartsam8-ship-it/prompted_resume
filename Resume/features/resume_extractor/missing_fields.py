from typing import Dict, List, Any
from Resume.features.resume_extractor.schema import RESUME_SCHEMA


class MissingFieldDetector:
    """
    Determines missing fields based on canonical resume schema.
    """

    @staticmethod
    def find_missing(resume_json: Dict[str, Any]) -> List[str]:
        missing = []

        for field, default in RESUME_SCHEMA.items():
            value = resume_json.get(field)

            if value is None:
                missing.append(field)
            elif isinstance(value, str) and value.strip() == "":
                missing.append(field)
            elif isinstance(value, list) and len(value) == 0:
                missing.append(field)
            elif isinstance(value, dict) and len(value) == 0:
                missing.append(field)

        return missing
