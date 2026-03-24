from Resume.features.chatbot.models import ChatState, ResumeData
from Resume.features.chatbot.prompt_builder import ResumePromptBuilder
from Resume.features.chatbot.sanitizer import InputSanitizer
from Resume.features.chatbot.state_store.base import StateStore
from Resume.features.chatbot.llm_schemas import ChatQuestionOutput, ChatValidationOutput
from Resume.core.interfaces import LLMClient


class ResumeChatbotService:
    def __init__(
        self,
        store: StateStore,
        llm: LLMClient,
        sanitizer: InputSanitizer,
    ):
        self.store = store
        self.llm = llm
        self.sanitizer = sanitizer

    # ---------- START OR RESUME ----------

    def start_or_resume(
        self,
        user_id: str,
        resume_json: dict,
        missing_fields: list[str]
    ) -> ChatState:

        state = self.store.get(user_id)
        if state:
            return state

        state = ChatState(
            user_id=user_id,
            resume=ResumeData(resume_json),
            pending_fields=missing_fields,
        )
        self.store.save(state)
        return state

    # ---------- NEXT QUESTION ----------

    async def next_question(self, state: ChatState) -> str | None:
        if not state.pending_fields:
            state.completed = True
            self.store.save(state)
            return None

        field = state.pending_fields[0]
        state.current_field = field
        self.store.save(state)

        prompt = ResumePromptBuilder.question_for_field(
            field, state.resume.data
        )
        raw = await self.llm.generate(prompt)
        return ChatQuestionOutput.parse_raw_text(raw).question

    # ---------- HANDLE USER INPUT ----------

    async def handle_user_input(
        self,
        state: ChatState,
        user_input: str
    ) -> dict:
        if not state.current_field:
            return {
                "status": "error",
                "message": "No active field to update. Please request the next question.",
            }

        field = state.current_field
        is_clean, sanitized = self.sanitizer.sanitize(user_input)
        if not is_clean:
            return {
                "status": "invalid",
                "question": sanitized,
                "field": field,
            }

        if sanitized.lower() == "skip":
            state.resume.data[field] = None
        else:
            validate_prompt = ResumePromptBuilder.validate_answer(
                field, sanitized
            )
            verdict_raw = await self.llm.generate(validate_prompt)
            verdict = ChatValidationOutput.parse_raw_text(verdict_raw)

            if verdict.verdict != "YES":
                raw = await self.llm.generate(
                    ResumePromptBuilder.reask_question(field)
                )
                return {
                    "status": "invalid",
                    "question": ChatQuestionOutput.parse_raw_text(raw).question,
                    "field": field,
                }

            state.resume.data[field] = sanitized

        # move forward
        state.pending_fields.pop(0)
        state.current_field = None

        if not state.pending_fields:
            state.completed = True

        self.store.save(state)

        if state.completed:
            return {
                "status": "completed",
                "resume": state.resume.data,
                "field": field,
            }

        return {"status": "next", "field": field}
