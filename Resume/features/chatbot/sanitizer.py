# features/chatbot/sanitizer.py
class InputSanitizer:
    BAD_WORDS = {
        "fuck", "shit", "bitch", "asshole", "idiot", "bastard"
    }

    def sanitize(self, text: str) -> tuple[bool, str]:
        lower = text.lower()
        if any(word in lower for word in self.BAD_WORDS):
            return False, (
                "Your message contains inappropriate language. "
                "Please respond respectfully."
            )
        return True, text.strip()
