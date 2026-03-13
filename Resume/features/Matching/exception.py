# semantic_matching/exceptions.py

class SemanticMatchingError(Exception):
    pass


class EmbeddingError(SemanticMatchingError):
    pass


class InvalidInputError(SemanticMatchingError):
    pass

class RepositoryError(SemanticMatchingError):
    pass