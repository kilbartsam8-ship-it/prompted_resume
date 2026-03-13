import numpy as np
from sentence_transformers import SentenceTransformer
from Resume.features.Matching.config import EMBEDDING_MODEL
from Resume.features.Matching.exception import EmbeddingError


class Encoder:
    _model = None

    def __init__(self):
        if Encoder._model is None:
            Encoder._model = SentenceTransformer(EMBEDDING_MODEL)

    async def encode(self, text: str) -> np.ndarray:
        try:
            vec = Encoder._model.encode([text])[0]
            return vec / (np.linalg.norm(vec) + 1e-12)
        except Exception as e:
            raise EmbeddingError(str(e))

    async def encode_batch(self, texts: list[str]) -> np.ndarray:
        try:
            vecs = Encoder._model.encode(texts)
            norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
            return vecs / norms
        except Exception as e:
            raise EmbeddingError(str(e))
