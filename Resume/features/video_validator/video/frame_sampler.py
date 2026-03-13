# features/video_validator/video/frame_sampler.py

from typing import Iterable, Iterator, Tuple


class FrameSampler:
    def __init__(self, fps: float, sample_fps: int):
        self.step = max(1, int(fps // sample_fps))

    def sample(self, frames: Iterable[Tuple[int, any]]) -> Iterator[Tuple[int, any]]:
        for idx, frame in frames:
            if idx % self.step == 0:
                yield idx, frame
