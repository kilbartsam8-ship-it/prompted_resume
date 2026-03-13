import numpy as np
from Resume.features.Matching.config import EUCLIDEAN_MAX_DISTANCE


def euclidean_score(a: np.ndarray, b: np.ndarray) -> float:
    dist = np.linalg.norm(a - b)
    return max(0.0, 1 - (dist / EUCLIDEAN_MAX_DISTANCE))
