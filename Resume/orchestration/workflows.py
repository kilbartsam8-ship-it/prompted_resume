from typing import Any

from Resume.core.llm_clients.groq_client import GroqLLMClient
from Resume.orchestration.pipelines import ResumeOnboardingPipeline


class ResumeOnboardingWorkflow:
    """
    Main business workflow up to finalized resume JSON.
    """

    def __init__(self):
        llm_client = GroqLLMClient()
        self.pipeline = ResumeOnboardingPipeline(llm_client=llm_client)

    async def start_resume_upload(
        self,
        user_id: str,
        file_path: str,
        file_type: str = "pdf",
    ) -> dict[str, Any]:
        return await self.pipeline.start(
            user_id=user_id,
            file_path=file_path,
            file_type=file_type,
        )

    async def submit_chatbot_answer(self, user_id: str, answer: str) -> dict[str, Any]:
        return await self.pipeline.submit_answer(user_id=user_id, answer=answer)

    async def choose_video_option(
        self,
        user_id: str,
        option: str,
        output_dir: str | None = None,
        voice_id: str = "female",
    ) -> dict[str, Any]:
        return await self.pipeline.choose_video_option(
            user_id=user_id,
            option=option,
            output_dir=output_dir,
            voice_id=voice_id,
        )

    async def submit_uploaded_video(self, user_id: str, video_path: str) -> dict[str, Any]:
        return await self.pipeline.submit_uploaded_video(
            user_id=user_id,
            video_path=video_path,
        )
