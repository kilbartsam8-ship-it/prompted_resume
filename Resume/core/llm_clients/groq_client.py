from langchain_groq import ChatGroq
from Resume.core.interfaces import LLMClient
from Resume.core.config import LLMConfig
from Resume.core.guardrails import guard_messages, guard_text


class GroqLLMClient(LLMClient):
    def __init__(self):
        self.client = ChatGroq(
            groq_api_key=LLMConfig.GROQ_API_KEY,
            model=LLMConfig.MODEL_NAME,
            temperature=LLMConfig.TEMPERATURE
        )

    async def generate(self, prompt) -> str:
        if isinstance(prompt, list):
            guarded, issues = guard_messages(prompt)
            if "prompt_injection" in issues or "toxicity" in issues:
                raise ValueError(f"LLM input blocked due to: {', '.join(sorted(set(issues)))}")
            result = await self.client.ainvoke(guarded)
        else:
            guarded, issues = guard_text(str(prompt))
            if "prompt_injection" in issues or "toxicity" in issues:
                raise ValueError(f"LLM input blocked due to: {', '.join(sorted(set(issues)))}")
            result = await self.client.ainvoke(guarded)
        return result.content
