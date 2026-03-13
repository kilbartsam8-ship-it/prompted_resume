import asyncio
import json
import os
from typing import Literal, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from Resume.features.ai_video_generation.exception import ScriptGenerationError


class IntroScriptResponse(BaseModel):
    script: str = Field(description="Final spoken first-person introduction script.")
    highlights: list[str] = Field(default_factory=list, description="Top achievements or strengths.")
    tone: str = Field(default="professional", description="Detected tone of the script.")


class IntroScriptGenerator:
    def __init__(
        self,
        api_base: Optional[str],
        api_key: str,
        model: str,
        provider: Literal["groq", "openai", "anthropic"] = "groq",
        temperature: float = 0.7,
    ):
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.provider = (provider or os.getenv("AI_VIDEO_LLM_PROVIDER", "groq")).lower()
        self.temperature = temperature
        self.llm = self._build_llm()

    def _build_llm(self):
        if self.provider == "groq":
            try:
                from langchain_groq import ChatGroq
            except Exception as e:
                raise ScriptGenerationError(
                    "Provider 'groq' dependencies failed to import. "
                    "Check langchain/transformers/torch compatibility in this environment."
                ) from e
            return ChatGroq(
                groq_api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
            )

        if self.provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError as e:
                raise ScriptGenerationError(
                    "Provider 'openai' requires 'langchain-openai'. Install it first."
                ) from e
            return ChatOpenAI(
                api_key=self.api_key,
                base_url=self.api_base or None,
                model=self.model,
                temperature=self.temperature,
            )

        if self.provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError as e:
                raise ScriptGenerationError(
                    "Provider 'anthropic' requires 'langchain-anthropic'. Install it first."
                ) from e
            return ChatAnthropic(
                api_key=self.api_key,
                model=self.model,
                temperature=self.temperature,
            )

        raise ScriptGenerationError(
            f"Unsupported provider '{self.provider}'. Use groq, openai, or anthropic."
        )

    def _build_messages(self, resume_json: dict):
        prompt = (
            "Create a concise, professional interview self-introduction "
            "(30-60 seconds). Focus on education, key skills, experience, "
            "projects, and career goals.\n\n"
            "Output rules:\n"
            "- Use a natural first-person speaking style.\n"
            "- No markdown, no bullet points, no headings.\n\n"
            f"Resume:\n{json.dumps(resume_json, indent=2)}"
        )

        return [
            SystemMessage(content="You are a professional interview coach."),
            HumanMessage(content=prompt),
        ]

    async def agenerate_structured(self, resume_json: dict) -> IntroScriptResponse:
        try:
            structured_llm = self.llm.with_structured_output(IntroScriptResponse)
            response = await structured_llm.ainvoke(self._build_messages(resume_json))
            response.script = self._normalize_script(response.script)
            return response
        except Exception as e:
            raise ScriptGenerationError(str(e))

    async def agenerate_text(self, resume_json: dict) -> str:
        response = await self.agenerate_structured(resume_json)
        return response.script

    def generate(self, resume_json: dict) -> str:
        return asyncio.run(self.agenerate_text(resume_json))

    def generate_structured(self, resume_json: dict) -> dict:
        response = asyncio.run(self.agenerate_structured(resume_json))
        return response.model_dump()

    @staticmethod
    def _normalize_script(raw: str) -> str:
        script = (raw or "").strip()

        if script.startswith("```") and script.endswith("```"):
            script = script.strip("`").strip()

        lines = [ln.strip() for ln in script.splitlines() if ln.strip()]
        if len(lines) > 1 and lines[0].endswith(":"):
            script = " ".join(lines[1:])
        else:
            script = " ".join(lines)

        if len(script) >= 2 and script[0] == '"' and script[-1] == '"':
            script = script[1:-1].strip()

        return script.strip()
