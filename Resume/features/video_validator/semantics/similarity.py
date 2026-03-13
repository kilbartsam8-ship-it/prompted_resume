# features/semantic_matching/similarity.py

import numpy as np


class SimilarityCalculator:
    @staticmethod
    def cosine(vec1, vec2) -> float:
        return float(np.dot(vec1, vec2))

    @staticmethod
    def euclidean(vec1, vec2) -> float:
        return float(np.linalg.norm(vec1 - vec2))
