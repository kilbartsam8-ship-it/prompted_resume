from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, field_validator

try:
    import email_validator  # type: ignore
    EMAIL_FIELD_TYPE = EmailStr
except ImportError:
    EMAIL_FIELD_TYPE = str


class ResumeSchema(BaseModel):
    classification: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EMAIL_FIELD_TYPE] = None
    phone: Optional[str] = None
    profile_links: Optional[Dict[str, str]] = None

    technical_skills: Optional[List[str]] = None
    soft_skills: Optional[List[str]] = None

    education: Optional[List[dict]] = None
    projects: Optional[List[dict]] = None
    experience: Optional[List[dict]] = None
    internships: Optional[List[dict]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None

    summary: Optional[str] = None
    current_location: Optional[str] = None

    current_ctc: Optional[str] = None
    expected_ctc: Optional[str] = None
    notice_period: Optional[str] = None
    work_mode: Optional[str] = None
    preferred_location: Optional[str] = None

    model_config = {
        "extra": "forbid",
    }

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value
        if not value.replace("+", "").replace("-", "").isdigit():
            raise ValueError("Invalid phone number format.")
        return value
