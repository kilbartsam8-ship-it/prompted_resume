from Resume.features.chatbot.models import ChatState
from Resume.features.chatbot.state_store.base import StateStore


class MemoryStateStore(StateStore):
    def __init__(self):
        self._state: dict[str, ChatState] = {}

    def get(self, user_id: str) -> ChatState | None:
        return self._state.get(user_id)

    def save(self, state: ChatState) -> None:
        self._state[state.user_id] = state

    def delete(self, user_id: str) -> None:
        self._state.pop(user_id, None)
