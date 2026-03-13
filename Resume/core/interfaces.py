from abc import ABC, abstractmethod
from typing import Any


class LLMClient(ABC):
    """
    Abstract LLM client interface.
    """

    @abstractmethod
    async def generate(self, prompt: Any) -> str:
        pass
