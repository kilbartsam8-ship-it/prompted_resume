import re


class TextCleaner:
    @staticmethod
    def clean_text(s: str) -> str:
        if not s:
            return ""
        s = re.sub(r"<[^>]+>", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    @staticmethod
    def list_to_text(lst):
        if not lst:
            return ""
        return ", ".join(TextCleaner.clean_text(str(x)) for x in lst)
