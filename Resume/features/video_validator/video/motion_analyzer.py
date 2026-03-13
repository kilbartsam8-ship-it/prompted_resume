# features/video_validator/video/motion_analyzer.py

import numpy as np
from typing import List, Tuple


class MotionAnalyzer:
    def compute(self, centers: List[Tuple[int, int]]) -> float:
        if len(centers) < 2:
            return 0.0

        deltas = [
            np.linalg.norm(
                np.array(centers[i]) - np.array(centers[i - 1])
            )
            for i in range(1, len(centers))
        ]

        return float(np.std(deltas))
