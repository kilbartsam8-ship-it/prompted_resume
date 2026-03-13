# features/video_validator/audio/resampler.py

import librosa
import soundfile as sf


class AudioResampler:
    def resample(self, input_wav: str, output_wav: str, target_sr: int):
        audio, sr = librosa.load(input_wav, sr=None)
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)
        sf.write(output_wav, audio, target_sr)
