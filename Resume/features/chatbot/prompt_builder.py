import json


class ResumePromptBuilder:

    @staticmethod
    def question_for_field(field: str, resume: dict) -> str:
        return (
            "You are a professional resume assistant.\n"
            "Ask ONE clear and concise question to fill the missing field.\n\n"
            "Return ONLY valid JSON with this exact shape:\n"
            '{"question":"<your question>"}\n\n'
            f"Field: {field}\n"
            f"Current resume data:\n{json.dumps(resume, indent=2)}"
        )

    @staticmethod
    def validate_answer(field: str, answer: str) -> str:
        return (
            "You are validating a resume response.\n"
            "Return ONLY valid JSON with this exact shape:\n"
            '{"verdict":"YES"} or {"verdict":"NO"}\n\n'
            f"Field: {field}\n"
            f"User answer: {answer}\n"
        )

    @staticmethod
    def reask_question(field: str) -> str:
        return (
            "The previous answer was inappropriate or invalid.\n"
            "Politely re-ask the question for the field.\n"
            "Return ONLY valid JSON with this exact shape:\n"
            '{"question":"<your question>"}\n\n'
            f"Field: {field}\n"
        )
