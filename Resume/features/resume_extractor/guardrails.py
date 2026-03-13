import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailIssue:
    code: str
    reason: str


class ResumeGuardrailScanner:
    _THREAT_PATTERNS: dict[str, tuple[str, ...]] = {
        "prompt_injection": (
            r"ignore\s+previous\s+instructions",
            r"system\s+prompt",
            r"developer\s+message",
            r"follow\s+these\s+instructions\s+instead",
        ),
        "jailbreaking": (
            r"\bDAN\b",
            r"jailbreak",
            r"bypass\s+safety",
            r"disable\s+guardrails",
        ),
        "sensitive_information_disclosure": (
            r"api[_\s-]?key",
            r"access[_\s-]?token",
            r"private[_\s-]?key",
            r"password\s*[:=]",
            r"\bsecret\b",
        ),
        "connecting_systems_excessive_agency": (
            r"execute\s+command",
            r"run\s+(?:shell|bash|powershell)",
            r"send\s+http\s+request",
            r"\bcurl\b",
            r"\bwget\b",
            r"\bssh\b",
        ),
        "training_data_poisoning": (
            r"add\s+this\s+to\s+training\s+data",
            r"poison\s+training",
            r"fine[-\s]?tune\s+on\s+this",
        ),
        "model_theft_inversion": (
            r"reveal\s+model\s+weights",
            r"extract\s+model",
            r"reconstruct\s+training\s+data",
            r"leak\s+hidden\s+prompt",
        ),
        "llmjacking": (
            r"use\s+my\s+api\s+key\s+to\s+proxy",
            r"mass\s+generate\s+requests",
            r"abuse\s+inference\s+endpoint",
            r"botnet",
        ),
    }

    _RESUME_HINTS = {
        "experience",
        "education",
        "skills",
        "project",
        "internship",
        "certification",
        "summary",
        "resume",
        "curriculum vitae",
        "linkedin",
    }

    def scan(self, text: str, is_image_based_pdf: bool) -> list[GuardrailIssue]:
        issues: list[GuardrailIssue] = []
        normalized = (text or "").strip()
        lower = normalized.lower()

        if is_image_based_pdf:
            issues.append(
                GuardrailIssue(
                    code="image_based_pdf",
                    reason="Uploaded PDF appears to be image-based/scanned and is not reliably machine-readable.",
                )
            )

        if not self._looks_like_resume(lower):
            issues.append(
                GuardrailIssue(
                    code="not_resume",
                    reason="Uploaded document does not look like a resume/CV.",
                )
            )

        for code, patterns in self._THREAT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized, flags=re.IGNORECASE):
                    issues.append(
                        GuardrailIssue(
                            code=code,
                            reason=f"Detected risky content pattern: {code}.",
                        )
                    )
                    break

        return issues

    def _looks_like_resume(self, text: str) -> bool:
        if len(text.split()) < 40:
            return False

        matches = sum(1 for hint in self._RESUME_HINTS if hint in text)
        return matches >= 2
