class ResumeExtractionError(Exception):
    """Base exception for resume extraction failures."""


class ResumeInputError(ResumeExtractionError):
    """Raised when extraction input is invalid."""


class ResumeParseError(ResumeExtractionError):
    """Raised when the resume file cannot be parsed reliably."""


class ResumeLLMOutputError(ResumeExtractionError):
    """Raised when LLM extraction output is invalid."""


class ResumeSecurityError(ResumeExtractionError):
    """Raised when guardrail or security checks fail."""
