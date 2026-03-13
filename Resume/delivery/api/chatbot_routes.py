import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Resume.core.llm_clients.groq_client import GroqLLMClient
from Resume.features.chatbot.sanitizer import InputSanitizer
from Resume.features.chatbot.service import ResumeChatbotService
from Resume.features.chatbot.state_store.memory_store import MemoryStateStore


app = FastAPI(title="Chatbot API")
store = MemoryStateStore()
service = ResumeChatbotService(
    store=store,
    llm=GroqLLMClient(),
    sanitizer=InputSanitizer(),
)


class ChatbotStartBody(BaseModel):
    user_id: str = Field(..., description="User identifier")
    resume_json: dict = Field(..., description="Current resume JSON object")
    missing_fields: list[str] = Field(default_factory=list, description="Missing resume fields")


class ChatbotAnswerBody(BaseModel):
    user_id: str = Field(..., description="User identifier")
    answer: str = Field(..., description="Answer for current missing field")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/chatbot/start")
async def chatbot_start(body: ChatbotStartBody):
    user_id = body.user_id
    state = service.start_or_resume(user_id, body.resume_json, body.missing_fields)

    if state.completed or not state.pending_fields:
        return {
            "status": "completed",
            "resume": state.resume.data,
        }

    try:
        question = await service.next_question(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate chatbot question: {exc}") from exc

    if question is None:
        return {
            "status": "completed",
            "resume": state.resume.data,
        }

    return {
        "status": "awaiting_answer",
        "question": question,
        "current_field": state.current_field,
        "missing_fields": list(state.pending_fields),
        "resume": state.resume.data,
    }


@app.post("/chatbot/answer")
async def chatbot_answer(body: ChatbotAnswerBody):
    user_id = body.user_id
    state = store.get(user_id)
    if not state:
        raise HTTPException(status_code=404, detail="No active chatbot session for this user.")

    try:
        result = await service.handle_user_input(state, body.answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process chatbot answer: {exc}") from exc

    if isinstance(result, str):
        return {
            "status": "awaiting_answer",
            "question": result,
            "current_field": state.current_field,
            "missing_fields": list(state.pending_fields),
            "resume": state.resume.data,
        }

    if result.get("status") == "completed":
        return result

    try:
        question = await service.next_question(state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate chatbot question: {exc}") from exc

    if question is None:
        return {
            "status": "completed",
            "resume": state.resume.data,
        }

    return {
        "status": "awaiting_answer",
        "question": question,
        "current_field": state.current_field,
        "missing_fields": list(state.pending_fields),
        "resume": state.resume.data,
    }


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