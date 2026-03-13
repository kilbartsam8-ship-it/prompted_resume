import subprocess
from Resume.features.ai_video_generation.exception import VideoRenderError


class VideoRenderer:
    @staticmethod
    def _escape_subtitles_path(srt_path: str) -> str:
        normalized = srt_path.replace("\\", "/")
        normalized = normalized.replace(":", r"\:")
        normalized = normalized.replace("'", r"\'")
        return normalized

    def render(self, audio_path: str, srt_path: str, output_path: str):
        escaped_srt = self._escape_subtitles_path(srt_path)

        cmd = [
            "ffmpeg", "-y",
            "-i", audio_path,
            "-filter_complex",
            (
                "color=c=black:s=1280x720[bg];"
                "[0:a]showwaves=s=600x600:mode=line:rate=60:colors=0x00ccff|0x00ffff[wave];"
                "[wave]format=rgba[circle_src];"
                "[circle_src]geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
                "a='if(gt((X-300)*(X-300)+(Y-300)*(Y-300),300*300),0,255)'[circle];"
                "[bg][circle]overlay=(W-w)/2:(H-h)/2,subtitles='" + escaped_srt + "'"
            ),
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            stderr_tail = (e.stderr or "").strip()[-1200:]
            raise VideoRenderError(
                f"ffmpeg failed with exit code {e.returncode}. "
                f"Command: {' '.join(cmd)}\n\nffmpeg stderr:\n{stderr_tail}"
            )
        except Exception as e:
            raise VideoRenderError(str(e))
