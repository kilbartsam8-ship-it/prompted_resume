# features/moderation/rules.py

PROFANITY_WORDS = {
    "fuck", "shit", "bitch", "asshole", "bastard", "idiot"
}

HATE_PATTERNS = [
    r"\bkill\b",
    r"\bhate\b",
    r"\bdestroy\b"
]

SEXUAL_PATTERNS = [
    r"\bnude\b",
    r"\bsex\b",
    r"\bporn\b"
]
