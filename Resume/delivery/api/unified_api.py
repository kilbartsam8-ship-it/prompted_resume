import sys
from pathlib import Path

from fastapi import FastAPI

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Resume.delivery.api.resume_extraction_api import app as resume_extraction_app
from Resume.delivery.api.video_validation_api import app as video_validation_app
from Resume.delivery.api.ai_video_generation_api import app as ai_video_generation_app
from Resume.delivery.api.chatbot_routes import app as chatbot_app
from Resume.delivery.api.response_utils import (
    register_exception_handlers,
    success_response,
)

app = FastAPI(title="Unified Resume Platform API")
register_exception_handlers(app)

# Include all sub-app routes on a single port without mounting sub-apps.
app.include_router(resume_extraction_app.router, prefix="/resume-api", tags=["resume"])
app.include_router(video_validation_app.router, prefix="/video-api", tags=["video"])
app.include_router(ai_video_generation_app.router, prefix="/ai-video-api", tags=["ai-video"])
app.include_router(chatbot_app.router, prefix="/chatbot-api", tags=["chatbot"])


@app.get("/health")
async def health() -> dict:
    return success_response("Health check successful.", 200, {"status": "ok"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("unified_api:app", host="0.0.0.0", port=8000, reload=True)
