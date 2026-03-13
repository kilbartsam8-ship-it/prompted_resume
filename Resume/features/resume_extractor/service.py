from pathlib import Path

from .parser import ResumeParser
from .pdf_validator import PDFValidator
from .link_classifier import LinkClassifier
from .duration_parser import DurationParser
from .llm_extractor import ResumeLLMExtractor
from .models import ParsedResume
from .guardrails import ResumeGuardrailScanner
from .exceptions import (
    ResumeInputError,
    ResumeParseError,
    ResumeLLMOutputError,
    ResumeSecurityError,
)

from Resume.core.llm_clients.groq_client import GroqLLMClient
from Resume.features.resume_extractor.missing_fields import MissingFieldDetector


class ResumeExtractionService:
    """
    Full resume extraction pipeline.
    """
    SUPPORTED_FILE_TYPES = {"pdf", "docx", "txt"}

    def __init__(self):
        self.parser = ResumeParser()
        self.pdf_validator = PDFValidator()
        self.link_classifier = LinkClassifier()
        self.duration_parser = DurationParser()
        self.guardrail_scanner = ResumeGuardrailScanner()

        llm_client = GroqLLMClient()
        self.llm_extractor = ResumeLLMExtractor(llm_client)

    async def extract_full(self, file_path: str, file_type: str = "pdf") -> dict:
        file_type = self._validate_inputs(file_path, file_type)
        parsed = self.parser.parse(file_path, file_type)
        self._validate_parsed_resume(parsed, file_path)

        if file_type == "pdf":
            parsed.is_scanned_pdf = self.pdf_validator.is_image_based_pdf(
                file_path, parsed.text
            )
        else:
            parsed.is_scanned_pdf = False

        parsed.classified_links = self.link_classifier.classify(parsed.links)
        self._run_guardrails(parsed)

        resume_json = await self.llm_extractor.extract(
            resume_text=parsed.text,
            structured_links=parsed.classified_links
        )
        self._validate_extraction_output(resume_json)

        missing_fields = MissingFieldDetector.find_missing(resume_json)

        return {
            "resume_json": resume_json,
            "missing_fields": missing_fields
        }

    def _validate_inputs(self, file_path: str, file_type: str) -> str:
        if not isinstance(file_path, str) or not file_path.strip():
            raise ResumeInputError("file_path must be a non-empty string.")

        normalized_type = (file_type or "").strip().lower()
        if normalized_type not in self.SUPPORTED_FILE_TYPES:
            supported = ", ".join(sorted(self.SUPPORTED_FILE_TYPES))
            raise ResumeInputError(
                f"Unsupported file_type '{file_type}'. Supported values: {supported}."
            )

        candidate = Path(file_path)
        if not candidate.exists() or not candidate.is_file():
            raise ResumeInputError(f"Resume file not found: {file_path}")

        if candidate.stat().st_size == 0:
            raise ResumeInputError(f"Resume file is empty: {file_path}")

        return normalized_type

    @staticmethod
    def _validate_parsed_resume(parsed: ParsedResume, file_path: str):
        if parsed is None:
            raise ResumeParseError("Parser returned no result.")

        parsed_text = (parsed.text or "").strip()
        if parsed_text.startswith("__READ_ERROR__"):
            raise ResumeParseError(f"Failed to parse resume: {parsed_text}")

        if not parsed_text:
            raise ResumeParseError(f"No readable text extracted from resume: {file_path}")

    @staticmethod
    def _validate_extraction_output(resume_json: dict):
        if not isinstance(resume_json, dict):
            raise ResumeLLMOutputError("LLM extraction output must be a JSON object.")

        if resume_json.get("error"):
            raw = (resume_json.get("raw_response") or "").strip()
            snippet = raw[:2000] + ("..." if len(raw) > 2000 else "")
            msg = f"LLM extraction failed: {resume_json.get('error')}"
            if snippet:
                msg = f"{msg}. Raw response snippet: {snippet}"
            raise ResumeLLMOutputError(msg)

    def _run_guardrails(self, parsed: ParsedResume):
        issues = self.guardrail_scanner.scan(
            text=parsed.text,
            is_image_based_pdf=bool(parsed.is_scanned_pdf),
        )
        if not issues:
            return

        details = "; ".join(f"{x.code}: {x.reason}" for x in issues)
        raise ResumeSecurityError(
            f"Resume declined. Please re-upload a valid resume PDF. Reasons: {details}"
        )
