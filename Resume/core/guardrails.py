import os
import re
from typing import Iterable, List


PII_EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PII_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")

INJECTION_PATTERNS = [
    r"ignore (all|any|previous) instructions",
    r"disregard (all|any|previous) instructions",
    r"system prompt",
    r"developer message",
    r"you are chatgpt",
    r"jailbreak",
    r"do anything now",
]

TOXICITY_PATTERNS = [
    r"\bkill\b",
    r"\bhate\b",
    r"\bgenocide\b",
    r"\bracist\b",
    r"\bterrorist\b",
]


def _max_chars() -> int:
    return int(os.getenv("LLM_MAX_INPUT_CHARS", "12000") or "12000")


def redact_pii(text: str) -> str:
    if (os.getenv("LLM_REDACT_PII", "true") or "").strip().lower() in {"0", "false", "no"}:
        return text
    text = PII_EMAIL.sub("[REDACTED_EMAIL]", text)
    text = PII_PHONE.sub("[REDACTED_PHONE]", text)
    return text


def detect_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pat, lowered) for pat in INJECTION_PATTERNS)


def detect_toxicity(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pat, lowered) for pat in TOXICITY_PATTERNS)


def enforce_length(text: str) -> str:
    limit = _max_chars()
    if len(text) <= limit:
        return text
    return text[:limit]


def guard_text(text: str) -> tuple[str, List[str]]:
    issues: List[str] = []
    if detect_prompt_injection(text):
        issues.append("prompt_injection")
    if detect_toxicity(text):
        issues.append("toxicity")
    sanitized = redact_pii(text)
    sanitized = enforce_length(sanitized)
    return sanitized, issues


def guard_messages(messages: Iterable) -> tuple[list, List[str]]:
    issues: List[str] = []
    guarded = []
    for msg in messages:
        content = getattr(msg, "content", "")
        new_content, msg_issues = guard_text(content)
        if msg_issues:
            issues.extend(msg_issues)
        if hasattr(msg, "copy"):
            guarded.append(msg.copy(update={"content": new_content}))
        else:
            guarded.append(msg.__class__(content=new_content))
    return guarded, issues
