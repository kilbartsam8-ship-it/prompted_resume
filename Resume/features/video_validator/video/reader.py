# features/video_validator/video/reader.py

import cv2
from typing import Iterator, Tuple


class VideoReader:
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

    def fps(self) -> float:
        return self.cap.get(cv2.CAP_PROP_FPS)

    def total_frames(self) -> int:
        return int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def read_frames(self) -> Iterator[Tuple[int, any]]:
        frame_idx = 0
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame_idx, frame
            frame_idx += 1

    def release(self):
        self.cap.release()
