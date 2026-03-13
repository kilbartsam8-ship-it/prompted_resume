from Resume.features.Matching.config import COSINE_WEIGHT, EUCLIDEAN_WEIGHT


def aggregate(cosine: float, euclidean: float) -> float:
    return round((cosine * COSINE_WEIGHT + euclidean * EUCLIDEAN_WEIGHT) * 100, 2)
