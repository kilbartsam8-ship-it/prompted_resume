# features/semantic_matching/embedder.py

from sentence_transformers import SentenceTransformer
from Resume.features.video_validator.semantics.config import DEFAULT_EMBEDDING_MODEL


class TextEmbedder:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model = SentenceTransformer(model_name)

    def embed(self, text: str):
        return self.model.encode(text, normalize_embeddings=True)
