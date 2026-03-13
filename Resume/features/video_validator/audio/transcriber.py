# features/video_validator/audio/transcriber.py

from typing import Tuple
import torch
import whisper


class WhisperTranscriber:
    def __init__(self, model_name: str, device: str):
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
        self.model = whisper.load_model(model_name, device=device)

    def transcribe(self, wav_path: str) -> Tuple[str, str]:
        result = self.model.transcribe(wav_path)
        return result["text"], result.get("language")
