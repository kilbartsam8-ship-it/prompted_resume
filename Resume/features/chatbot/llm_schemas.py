import json
import re
from typing import Literal

from pydantic import BaseModel


class ChatQuestionOutput(BaseModel):
    question: str

    @classmethod
    def parse_raw_text(cls, raw: str) -> "ChatQuestionOutput":
        payload = _extract_json_object(raw)
        return cls.model_validate(payload)


class ChatValidationOutput(BaseModel):
    verdict: Literal["YES", "NO"]

    @classmethod
    def parse_raw_text(cls, raw: str) -> "ChatValidationOutput":
        payload = _extract_json_object(raw)
        return cls.model_validate(payload)


def _extract_json_object(raw: str) -> dict:
    if not isinstance(raw, str):
        raise ValueError("LLM output must be a string")

    text = raw.strip()
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in LLM output")

    return json.loads(match.group(0))
