import asyncio
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from Resume.features.resume_extractor.service import ResumeExtractionService
from Resume.features.chatbot.service import ResumeChatbotService
from Resume.features.chatbot.state_store.memory_store import MemoryStateStore
from Resume.features.chatbot.sanitizer import InputSanitizer
from Resume.features.video_validator.service import VideoValidationService
from Resume.features.ai_video_generation.config import (
    DEFAULT_LLM_MODEL,
    DEFAULT_TTS_MODEL,
)
from Resume.features.ai_video_generation.llm.script_generator import IntroScriptGenerator
from Resume.features.ai_video_generation.audio.tts_engine import TTSEngine
from Resume.features.ai_video_generation.subtitles.srt_generator import SRTGenerator
from Resume.features.ai_video_generation.video.renderer import VideoRenderer
from Resume.core.llm_clients.groq_client import GroqLLMClient


def _save_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


async def run_full_flow():
    print("\nResume Flow (Terminal)")
    print("=" * 60)
    

    # 1) Upload resume and extract
    file_path = input("Enter resume file path: ").strip()
    file_type = input("Enter file type (pdf/docx/txt): ").strip().lower() or "pdf"

    resume_service = ResumeExtractionService()
    extraction = await resume_service.extract_full(
        file_path=file_path,
        file_type=file_type,
    )
    resume_json = extraction.get("resume_json", {})
    missing_fields = extraction.get("missing_fields", [])

    print("\nExtraction complete.")
    print(f"Missing fields: {missing_fields}")

    # 2) Chatbot fill missing fields
    store = MemoryStateStore()
    bot = ResumeChatbotService(
        store=store,
        llm=GroqLLMClient(),
        sanitizer=InputSanitizer(),
    )
    user_id = "local_user"
    state = bot.start_or_resume(user_id, resume_json, missing_fields)

    question = await bot.next_question(state)
    while True:
        if question is None:
            print("\nAll missing fields completed.")
            break
        print(f"\nLLM: {question}")
        answer = input("You (type 'skip' to skip): ").strip()
        response = await bot.handle_user_input(state, answer)
        if response.get("status") == "invalid":
            question = response.get("question")
            continue
        if response.get("status") == "error":
            print(f"Notice: {response.get('message')}")
            break
        if response.get("status") == "completed":
            break
        question = await bot.next_question(state)

    filled_resume = state.resume.data
    print("\nFilled Resume JSON")
    print(json.dumps(filled_resume, indent=2))

    # 3) Choose video option
    print("\nChoose video option")
    print("1. AI video generation")
    print("2. Upload video for validation")
    choice = input("Select (1/2): ").strip()

    if choice == "1":
        output_dir = input("Output directory (default: ./tmp/ai_video_output): ").strip()
        output_dir = output_dir or str(PROJECT_ROOT / "tmp" / "ai_video_output")
        os.makedirs(output_dir, exist_ok=True)

        api_base = os.getenv("AI_VIDEO_LLM_API_BASE") or input(
            "Enter LLM API base (e.g., https://api.groq.com/openai/v1): "
        ).strip()
        api_key = (
            os.getenv("AI_VIDEO_LLM_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or input("Enter LLM API key: ").strip()
        )
        llm_model = os.getenv("AI_VIDEO_LLM_MODEL") or DEFAULT_LLM_MODEL

        tts_model = os.getenv("AI_VIDEO_TTS_MODEL") or DEFAULT_TTS_MODEL
        use_gpu = (os.getenv("AI_VIDEO_TTS_GPU") or "false").strip().lower() in {"1", "true", "yes"}
        voice_choice = (os.getenv("AI_VIDEO_TTS_VOICE") or "female").strip().lower()

        if not api_base:
            print("Missing API base.")
            return
        if not api_key:
            print("Missing API key.")
            return

        script_generator = IntroScriptGenerator(
            api_base=api_base,
            api_key=api_key,
            model=llm_model,
        )
        tts_engine = TTSEngine(
            model_name=tts_model,
            gpu=use_gpu,
            speaker=voice_choice,
        )
        srt_generator = SRTGenerator()
        video_renderer = VideoRenderer()

        script_path = os.path.join(output_dir, "intro_script.txt")
        srt_path = os.path.join(output_dir, "intro_subtitles.srt")
        video_path = os.path.join(output_dir, "intro_video.mp4")
        manifest_path = os.path.join(output_dir, "generation_result.json")

        script = await script_generator.agenerate_text(filled_resume)
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)

        audio_artifact = tts_engine.synthesize(
            text=script,
            output_dir=output_dir,
            filename="intro_audio.wav",
            voice_id=voice_choice,
        )

        srt_generator.generate(audio_artifact, script, srt_path)
        video_renderer.render(audio_artifact.path, srt_path, video_path)

        result = {
            "intro_script": script,
            "artifacts": {
                "script_txt": script_path,
                "audio_wav": audio_artifact.path,
                "subtitles_srt": srt_path,
                "video_mp4": video_path,
            },
            "audio_metadata": {
                "duration_seconds": audio_artifact.duration_seconds,
                "sample_rate": audio_artifact.sample_rate,
                "voice_id": audio_artifact.voice_id,
                "language": audio_artifact.language,
            },
            "config": {
                "llm_model": llm_model,
                "tts_model_requested": tts_model,
                "tts_model_loaded": tts_engine.model_name,
                "tts_voice_choice": voice_choice,
                "gpu": use_gpu,
            },
        }

        _save_json(manifest_path, result)
        print("\nAI video generation completed.")
        print(json.dumps(result, indent=2))
        print(f"\nSaved result manifest: {manifest_path}")

    elif choice == "2":
        video_service = VideoValidationService()
        while True:
            video_path = input("Enter video file path: ").strip()
            result = await video_service.validate_video_async(video_path, filled_resume)
            print("\nVideo validation result")
            print(json.dumps(result, indent=2))

            if result.get("final_valid"):
                final_resume = result.get("resume_json", filled_resume)
                print("\nFinal Resume JSON (with video extraction if approved)")
                print(json.dumps(final_resume, indent=2))
                break

            retry = input("Video not approved. Re-upload a proper video? (y/n): ").strip().lower()
            if retry != "y":
                print("Exiting without approved video.")
                break
    else:
        print("Invalid option. Exiting.")


async def main():
    await run_full_flow()


if __name__ == "__main__":
    asyncio.run(main())
