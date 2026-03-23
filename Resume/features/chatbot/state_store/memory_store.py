from Resume.features.chatbot.models import ChatState
from Resume.features.chatbot.state_store.base import StateStore


class MemoryStateStore(StateStore):
    def __init__(self):
        self.store = {}

    def get(self, user_id: str) -> ChatState | None:
        return self.store.get(user_id)

    def save(self, state: ChatState) -> None:
        self.store[state.user_id] = state

    def delete(self, user_id: str) -> None:
        if user_id in self.store:
            del self.store[user_id]
