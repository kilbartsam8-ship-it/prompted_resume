import re

TOXIC_PATTERNS = {
    "profanity": [
        r"\bfuck\b",
        r"\bshit\b",
        r"\basshole\b",
    ],
    "hate": [
        r"\bhate\b",
    ],
}


def find_matches(text: str):
    matches = []
    for category, patterns in TOXIC_PATTERNS.items():
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                matches.append(category)
    return matches
