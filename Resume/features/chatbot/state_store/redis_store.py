import json
from redis import Redis
from Resume.features.chatbot.models import ChatState, ResumeData
from .base import StateStore


class RedisStateStore(StateStore):
    def __init__(self, redis: Redis):
        self.redis = redis

    def get(self, user_id: str) -> ChatState | None:
        raw = self.redis.get(user_id)
        if not raw:
            return None

        payload = json.loads(raw)
        return ChatState(
            user_id=user_id,
            resume=ResumeData(payload["resume"]),
            pending_fields=payload["pending_fields"],
            current_field=payload.get("current_field"),
            completed=payload.get("completed", False)
        )

    def save(self, state: ChatState) -> None:
        self.redis.set(
            state.user_id,
            json.dumps({
                "resume": state.resume.data,
                "pending_fields": state.pending_fields,
                "current_field": state.current_field,
                "completed": state.completed
            })
        )

    def delete(self, user_id: str) -> None:
        self.redis.delete(user_id)
