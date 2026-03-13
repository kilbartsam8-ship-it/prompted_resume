import json
import re
from typing import List, Dict
from langchain_core.messages import HumanMessage, SystemMessage
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from Resume.core.interfaces import LLMClient
from Resume.core.exceptions import ValidationError as CoreValidationError
from Resume.core.schemas.resume_schema import ResumeSchema
from Resume.core.validators.pydantic_validator import PydanticValidator
from Resume.features.resume_extractor.prompts.resume_extractor_prompt import RESUME_EXTRACTION_PROMPT


class ResumeLLMExtractor:
    """
    Uses an LLM to extract structured ATS-friendly resume data.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def extract(
        self,
        resume_text: str,
        structured_links: Dict,
        experiences: List[Dict] | None = None,
        internships: List[Dict] | None = None,
    ) -> Dict:

        experiences = experiences or []
        internships = internships or []

        prompt_messages = self._build_prompt(
            resume_text,
            structured_links,
            experiences,
            internships
        )

        raw_response = await self.llm.generate(prompt_messages)
        return self._safe_json(raw_response)

    # ---------------- private helpers ----------------

    def _build_prompt(
        self,
        resume_text: str,
        structured_links: Dict,
        experiences: List[Dict],
        internships: List[Dict],
    ):
        return [
            SystemMessage(content=RESUME_EXTRACTION_PROMPT),
            SystemMessage(content=f"Structured Links:\n{json.dumps(structured_links, indent=2)}"),
            SystemMessage(content=f"Experience (pre-parsed):\n{json.dumps(experiences, indent=2)}"),
            SystemMessage(content=f"Internships (pre-parsed):\n{json.dumps(internships, indent=2)}"),
            HumanMessage(content=resume_text),
        ]

    def _safe_json(self, text: str) -> Dict:
        """
        Extracts JSON safely from LLM output.
        """
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            return {
                "classification": "unknown",
                "error": "Invalid JSON returned by LLM",
                "raw_response": text,
            }

        try:
            payload = json.loads(match.group(0))

            # Normalize common alternate keys to match ResumeSchema
            key_map = {
                "languages_known": "languages",
                "hobbies_or_extracurriculars": "hobbies",
                "work_location_preference": "preferred_location",
                "total_experience": "experience",
            }
            for src, dest in key_map.items():
                if src in payload and dest not in payload:
                    payload[dest] = payload[src]
                if src in payload:
                    payload.pop(src, None)

            # Drop any extra top-level keys not in schema
            allowed = set(ResumeSchema.model_fields.keys())
            payload = {k: v for k, v in payload.items() if k in allowed}

            # Normalize phone to digits/+/- only
            phone = payload.get("phone")
            if isinstance(phone, str):
                cleaned = (
                    phone.replace(" ", "")
                    .replace("(", "")
                    .replace(")", "")
                )
                payload["phone"] = cleaned or phone

            return PydanticValidator.validate(ResumeSchema, payload)
        except json.JSONDecodeError:
            return {
                "classification": "unknown",
                "error": "JSON parsing failed",
                "raw_response": text,
            }
        except CoreValidationError:
            return {
                "classification": "unknown",
                "error": "Schema validation failed",
                "raw_response": text,
            }
