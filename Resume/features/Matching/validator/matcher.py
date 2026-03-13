import numpy as np
from typing import List
from Resume.features.Matching.models import MatchingScore
from Resume.features.Matching.similarity.cosine import cosine_similarity
from Resume.features.Matching.similarity.euclidean import euclidean_score
from Resume.features.Matching.similarity.aggregator import aggregate


class SemanticMatcher:
    def match(
        self,
        resume_embedding: np.ndarray,
        jd_embeddings: List[tuple]
    ) -> List[MatchingScore]:

        results = []

        for jd_id, jd_emb in jd_embeddings:
            cos = cosine_similarity(resume_embedding, jd_emb)
            euc = euclidean_score(resume_embedding, jd_emb)
            score = aggregate(cos, euc)

            results.append(MatchingScore(jd_id=jd_id, score=score))

        return sorted(results, key=lambda x: x.score, reverse=True)
