import os
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

from Resume.features.ai_video_generation.audio.audio_models import AudioArtifact
from Resume.features.ai_video_generation.audio.voice_registry import VoiceRegistry
from Resume.features.ai_video_generation.exception import TTSError


class TTSBackend(ABC):
    @abstractmethod
    def synthesize(self, text: str, voice_id: str, output_path: str) -> AudioArtifact:
        raise NotImplementedError


class ChatterboxBackend(TTSBackend):
    _models: Dict[str, Any] = {}
    _model_cls: Any = None

    def __init__(self, device: str):
        self.device = device

    @classmethod
    def _load_model_cls(cls):
        if cls._model_cls is not None:
            return cls._model_cls
        try:
            from chatterbox.tts import ChatterboxTTS
        except Exception as exc:
            raise TTSError(
                "Chatterbox TTS is unavailable in this environment. "
                "Check chatterbox/transformers/torch compatibility and reinstall dependencies."
            ) from exc
        cls._model_cls = ChatterboxTTS
        return cls._model_cls

    def _get_model(self):
        if self.device not in self._models:
            model_cls = self._load_model_cls()
            self._models[self.device] = model_cls.from_pretrained(device=self.device)
        return self._models[self.device]

    def synthesize(self, text: str, voice_id: str, output_path: str) -> AudioArtifact:
        voice = VoiceRegistry.get(voice_id)
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise TTSError("TTS input cannot be empty.")

        prompt_audio_path = voice.prompt_audio_path
        if voice.id == "male" and not prompt_audio_path:
            raise TTSError(
                "Male voice requires a prompt file. Set AI_VIDEO_TTS_MALE_PROMPT to a male reference WAV."
            )

        model = self._get_model()
        kwargs = {"text": cleaned_text}
        if prompt_audio_path:
            kwargs["audio_prompt_path"] = prompt_audio_path

        wav = model.generate(**kwargs)
        torchaudio = _load_torchaudio()
        torchaudio.save(output_path, wav, model.sr)

        samples = int(wav.shape[-1])
        return AudioArtifact(
            path=output_path,
            duration_seconds=samples / model.sr,
            sample_rate=model.sr,
            voice_id=voice.id,
        )


class TTSEngine:
    """
    Facade used by the AI video feature.
    Uses Chatterbox backend and supports male/female voice selection.
    """

    def __init__(
        self,
        model_name: str = "chatterbox",
        gpu: bool = False,
        speaker: Optional[str] = None,
        speed: Optional[float] = None,
        backend: Optional[TTSBackend] = None,
    ):
        # Kept for backward compatibility with existing callers.
        self.requested_model_name = model_name
        self.model_name = "chatterbox"
        self.speaker = speaker or os.getenv("AI_VIDEO_TTS_VOICE", "female")
        self.speed = 1.0

        if gpu:
            torch = _load_torch()
            device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device = "cpu"
        self.backend = backend or ChatterboxBackend(device=device)

    def synthesize(
        self,
        text: str,
        output_dir: str,
        filename: str,
        voice_id: Optional[str] = None,
    ) -> AudioArtifact:
        os.makedirs(output_dir, exist_ok=True)
        output_path = str(Path(output_dir) / filename)

        selected_voice = voice_id or self.speaker or "female"
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            raise TTSError("TTS input cannot be empty.")

        max_chars = int(os.getenv("AI_VIDEO_TTS_MAX_CHARS_PER_CHUNK", "500") or "500")
        chunks = self._chunk_text(cleaned_text, max_chars=max_chars)
        if len(chunks) == 1:
            return self.backend.synthesize(
                text=chunks[0],
                voice_id=selected_voice,
                output_path=output_path,
            )

        temp_paths: list[str] = []
        try:
            for idx, chunk in enumerate(chunks, 1):
                temp_path = str(Path(output_dir) / f"tts_part_{idx}.wav")
                temp_paths.append(temp_path)
                self.backend.synthesize(
                    text=chunk,
                    voice_id=selected_voice,
                    output_path=temp_path,
                )

            waveforms = []
            sample_rate = None
            torchaudio = _load_torchaudio()
            torch = _load_torch()
            for path in temp_paths:
                wav, sr = torchaudio.load(path)
                if sample_rate is None:
                    sample_rate = sr
                elif sr != sample_rate:
                    raise TTSError("Inconsistent sample rates between TTS chunks.")
                waveforms.append(wav)

            combined = torch.cat(waveforms, dim=-1)
            torchaudio.save(output_path, combined, sample_rate or 22050)

            samples = int(combined.shape[-1])
            return AudioArtifact(
                path=output_path,
                duration_seconds=samples / (sample_rate or 22050),
                sample_rate=sample_rate or 22050,
                voice_id=selected_voice,
            )
        finally:
            for path in temp_paths:
                try:
                    os.remove(path)
                except Exception:
                    pass

    @staticmethod
    def _chunk_text(text: str, max_chars: int) -> list[str]:
        if max_chars <= 0 or len(text) <= max_chars:
            return [text]

        sentences = []
        current = ""
        for part in text.replace("\n", " ").split(". "):
            part = part.strip()
            if not part:
                continue
            if current:
                candidate = current + ". " + part
            else:
                candidate = part
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    sentences.append(current + ".")
                current = part
        if current:
            if not current.endswith("."):
                current += "."
            sentences.append(current)

        chunks = []
        buffer = ""
        for sentence in sentences:
            if not buffer:
                buffer = sentence
                continue
            if len(buffer) + 1 + len(sentence) <= max_chars:
                buffer = buffer + " " + sentence
            else:
                chunks.append(buffer.strip())
                buffer = sentence
        if buffer:
            chunks.append(buffer.strip())

        return chunks


def _load_torch():
    try:
        import torch
    except Exception as exc:
        raise TTSError(
            "PyTorch failed to import. Check torch/torchaudio/numpy compatibility in this environment."
        ) from exc
    return torch


def _load_torchaudio():
    try:
        import torchaudio
    except Exception as exc:
        raise TTSError(
            "torchaudio failed to import. Check torch and torchaudio version compatibility."
        ) from exc
    return torchaudio
