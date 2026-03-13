# features/semantic_matching/matcher.py

from Resume.features.video_validator.semantics.embedder import TextEmbedder
from Resume.features.video_validator.semantics.similarity import SimilarityCalculator


class SemanticMatcher:
    def __init__(self, embedder: TextEmbedder):
        self.embedder = embedder

    def compare(self, text1: str, text2: str) -> float:
        vec1 = self.embedder.embed(text1)
        vec2 = self.embedder.embed(text2)
        return SimilarityCalculator.cosine(vec1, vec2)
