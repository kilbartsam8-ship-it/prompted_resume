from abc import ABC, abstractmethod
from Resume.features.chatbot.models import ChatState


class StateStore(ABC):
    @abstractmethod
    def get(self, user_id: str) -> ChatState | None:
        pass

    @abstractmethod
    def save(self, state: ChatState) -> None:
        pass

    @abstractmethod
    def delete(self, user_id: str) -> None:
        pass
