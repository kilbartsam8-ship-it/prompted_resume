# features/video_validator/audio/duration_analyzer.py

import librosa


class AudioDurationAnalyzer:
    def compute(self, wav_path: str) -> float:
        audio, sr = librosa.load(wav_path, sr=None)
        return len(audio) / sr
