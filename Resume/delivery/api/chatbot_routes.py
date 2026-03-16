import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from redis import Redis

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Resume.core.llm_clients.groq_client import GroqLLMClient
from Resume.features.chatbot.sanitizer import InputSanitizer
from Resume.features.chatbot.service import ResumeChatbotService
from Resume.features.chatbot.state_store.redis_store import RedisStateStore


app = FastAPI(title="Chatbot API")
redis_client = None


def _build_redis_client() -> Redis:
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return Redis.from_url(redis_url, decode_responses=True)

    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    password = os.getenv("REDIS_PASSWORD")
    return Redis(host=host, port=port, db=db, password=password, decode_responses=True)


redis_client = _build_redis_client()
store = RedisStateStore(redis_client)
service = ResumeChatbotService(
    store=store,
    llm=GroqLLMClient(),
    sanitizer=InputSanitizer(),
)


class ChatbotRequestBody(BaseModel):
    user_id: str = Field(..., description="User identifier")
    resume_json: dict | None = Field(default=None, description="Current resume JSON object")
    answer: str | None = Field(default=None, description="Answer for current missing field")

    @model_validator(mode="after")
    def _ensure_payload(self):
        if self.resume_json is None and self.answer is None:
            raise ValueError("Either resume_json or answer must be provided.")
        return self


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

def _state_payload(state, question: str | None = None) -> dict:
    payload = {
        "user_id": state.user_id,
        "current_field": state.current_field,
        "missing_fields": list(state.pending_fields),
        "completed": state.completed,
    }
    if question is not None:
        payload["question"] = question
    return payload


def _completed_payload(state) -> dict:
    payload = _state_payload(state)
    payload["resume"] = state.resume.data
    return payload


def _history_key(user_id: str) -> str:
    return f"chatbot:{user_id}:history"


def _store_history(user_id: str, entry_type: str, payload: dict) -> None:
    redis_client.rpush(
        _history_key(user_id),
        json.dumps({"type": entry_type, **payload}),
    )


@app.post("/chatbot")
async def chatbot(body: ChatbotRequestBody):
    user_id = body.user_id

    if body.resume_json is not None:
        missing_fields = body.resume_json.get("missing_fields", [])
        state = service.start_or_resume(user_id, body.resume_json, missing_fields)
    else:
        state = store.get(user_id)
        if not state:
            raise HTTPException(status_code=404, detail="No active chatbot session for this user.")

    if body.answer is not None:
        if state.current_field:
            _store_history(
                user_id,
                "answer",
                {"field": state.current_field, "answer": body.answer},
            )

        try:
            result = await service.handle_user_input(state, body.answer)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to process chatbot answer: {exc}") from exc

        if isinstance(result, str):
            _store_history(
                user_id,
                "question",
                {"field": state.current_field, "question": result},
            )
            return _state_payload(state, question=result)

        if result.get("status") == "completed":
            return _completed_payload(state)

    if state.completed or not state.pending_fields:
        return _completed_payload(state)

    try:
        question = await service.next_question(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate chatbot question: {exc}") from exc

    if question is None:
        return _completed_payload(state)

    _store_history(
        user_id,
        "question",
        {"field": state.current_field, "question": question},
    )
    return _state_payload(state, question=question)


@app.get("/chatbot/session/{user_id}")
async def chatbot_session(user_id: str):
    state = store.get(user_id)
    if not state:
        raise HTTPException(status_code=404, detail="No active chatbot session for this user.")

    return {
        "user_id": state.user_id,
        "current_field": state.current_field,
        "missing_fields": list(state.pending_fields),
        "completed": state.completed,
        "resume": state.resume.data,
    }


@app.delete("/chatbot/session/{user_id}")
async def chatbot_reset(user_id: str):
    store.delete(user_id)
    return {"status": "deleted", "user_id": user_id}

# if __name__ == "__main__":
#     uvicorn.run("chatbot_routes:app", host="0.0.0.0", port=8000, reload=True)
