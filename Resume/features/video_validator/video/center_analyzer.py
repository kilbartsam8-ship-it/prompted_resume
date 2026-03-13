# features/video_validator/video/center_analyzer.py

from typing import List, Tuple


class CenterAnalyzer:
    def compute(
        self,
        centers: List[Tuple[int, int]],
        frame_width: int,
        frame_height: int
    ) -> float:
        if not centers:
            return 1.0

        frame_center = (frame_width // 2, frame_height // 2)

        distances = [
            (
                abs(cx - frame_center[0]) / frame_width +
                abs(cy - frame_center[1]) / frame_height
            )
            for cx, cy in centers
        ]

        return sum(distances) / len(distances)
