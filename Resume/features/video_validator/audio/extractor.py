# features/video_validator/audio/extractor.py

import subprocess
from pathlib import Path


class AudioExtractor:
    def extract(self, video_path: str, output_wav: str):
        Path(output_wav).parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-i", video_path,
            "-ac", "1",
            "-ar", "16000",
            output_wav
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
