import re
from typing import List


class VideoExtractionService:
    """
    Builds a professional summary from validated video transcript text.
    """

    _FILLER_PATTERN = re.compile(
        r"\b(um+|uh+|hmm+|you know|like|i mean|sort of|kind of|basically|actually)\b",
        flags=re.IGNORECASE,
    )

    def extract_professional_summary(self, transcript: str, max_sentences: int = 4) -> str:
        cleaned = self._normalize(transcript)
        if not cleaned:
            return ""

        sentences = self._split_sentences(cleaned)
        selected = sentences[:max(1, max_sentences)]

        summary_body = " ".join(selected).strip()
        if not summary_body:
            return ""

        return f"The candidate presents a professional profile summary: {summary_body}"

    def _normalize(self, text: str) -> str:
        text = text or ""
        text = text.replace("\n", " ")
        text = self._FILLER_PATTERN.sub(" ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _split_sentences(self, text: str) -> List[str]:
        chunks = [s.strip(" -") for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if not chunks:
            chunks = [text]

        normalized: List[str] = []
        for sentence in chunks:
            sentence = re.sub(r"\s+", " ", sentence).strip()
            if not sentence:
                continue
            if sentence[-1] not in ".!?":
                sentence += "."
            sentence = sentence[0].upper() + sentence[1:]
            normalized.append(sentence)

        return normalized
