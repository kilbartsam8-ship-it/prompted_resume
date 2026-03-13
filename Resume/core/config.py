import os
from dotenv import load_dotenv

load_dotenv()


class LLMConfig:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODEL_NAME = "llama-3.3-70b-versatile"
    TEMPERATURE = 0
    MAX_INPUT_CHARS = int(os.getenv("LLM_MAX_INPUT_CHARS", "12000") or "12000")
