from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeExtractionOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    classification: str = "unknown"
    name: str = ""
    email: str = ""
    phone: str = ""
    profile_links: dict[str, Any] = Field(default_factory=dict)
    technical_skills: list[Any] = Field(default_factory=list)
    soft_skills: list[Any] = Field(default_factory=list)
    education: list[Any] = Field(default_factory=list)
    projects: list[Any] = Field(default_factory=list)
    experience: list[Any] = Field(default_factory=list)
    internships: list[Any] = Field(default_factory=list)
    certifications: list[Any] = Field(default_factory=list)
    languages: list[Any] = Field(default_factory=list)
    hobbies: list[Any] = Field(default_factory=list)
    summary: str = ""
    current_location: str = ""
    current_ctc: str = ""
    expected_ctc: str = ""
    notice_period: str = ""
    work_mode: str = ""
    preferred_location: str = ""
    video_summary: str = ""
