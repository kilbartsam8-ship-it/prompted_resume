import soundfile as sf
import srt
from pathlib import Path
from datetime import timedelta
from Resume.features.ai_video_generation.exception import SubtitleError
from Resume.features.ai_video_generation.audio.audio_models import AudioArtifact


class SRTGenerator:
    def __init__(self):
        torch = _load_torch()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def generate(self, audio: AudioArtifact, text: str, output_path: str) -> str:
        if not isinstance(audio, AudioArtifact):
            raise SubtitleError("audio must be an AudioArtifact.")
        if not text or not isinstance(text, str) or not text.strip():
            raise SubtitleError("Subtitle text cannot be empty.")
        if not output_path or not isinstance(output_path, str):
            raise SubtitleError("output_path must be a non-empty string.")

        audio_path = audio.path
        if not audio_path:
            raise SubtitleError("Audio artifact path is missing.")
        if not Path(audio_path).exists():
            raise SubtitleError(f"Audio file not found: {audio_path}")

        try:
            audio, sr = sf.read(audio_path)
            duration = len(audio) / sr
            subs = self._word_timed_subtitles(
                text=text,
                duration_seconds=duration,
                audio_path=audio_path,
            )

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(srt.compose(subs))

            return output_path
        except Exception as e:
            raise SubtitleError(str(e))

    def _word_timed_subtitles(
        self,
        text: str,
        duration_seconds: float,
        audio_path: str,
    ) -> list[srt.Subtitle]:
        # Best-effort alignment with whisperx; fallback is deterministic equal timing.
        try:
            whisperx = _load_whisperx()
            align_model, metadata = whisperx.load_align_model(
                language_code="en", device=self.device
            )
            segments = [{"text": text, "start": 0, "end": duration_seconds}]
            aligned = whisperx.align(
                segments, align_model, metadata, audio_path, self.device
            )
            subs = []
            idx = 1
            for seg in aligned.get("segments", []):
                for w in seg.get("words", []):
                    start = float(w.get("start", 0.0))
                    end = float(w.get("end", start + 0.25))
                    word = str(w.get("word", "")).strip()
                    if not word:
                        continue
                    subs.append(
                        srt.Subtitle(
                            index=idx,
                            start=timedelta(seconds=start),
                            end=timedelta(seconds=end),
                            content=word,
                        )
                    )
                    idx += 1
            if subs:
                return subs
        except Exception:
            pass

        words = [w for w in text.replace("\n", " ").split() if w.strip()]
        if not words:
            raise SubtitleError("No words available to generate subtitles.")

        words_per_line = 4
        groups = [
            " ".join(words[i:i + words_per_line])
            for i in range(0, len(words), words_per_line)
        ]
        slot = max(duration_seconds / max(len(groups), 1), 0.2)

        subs = []
        for idx, line in enumerate(groups, 1):
            start = (idx - 1) * slot
            end = min(idx * slot, duration_seconds)
            if end <= start:
                end = start + 0.2
            subs.append(
                srt.Subtitle(
                    index=idx,
                    start=timedelta(seconds=start),
                    end=timedelta(seconds=end),
                    content=line,
                )
            )
        return subs


def _load_torch():
    try:
        import torch
    except Exception as exc:
        raise SubtitleError(
            "PyTorch failed to import. Check torch/torchaudio/numpy compatibility."
        ) from exc
    return torch


def _load_whisperx():
    try:
        import whisperx
    except Exception as exc:
        raise SubtitleError(
            "whisperx failed to import. Check whisperx and PyTorch dependencies."
        ) from exc
    return whisperx
