# features/moderation/sanitizer.py

import re


class TextSanitizer:
    def normalize(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        return text.strip()
