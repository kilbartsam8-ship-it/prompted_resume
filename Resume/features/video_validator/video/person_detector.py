# features/video_validator/video/person_detector.py

from typing import Any, Dict, List, Tuple


class PersonDetector:
    def __init__(self, model):
        self.model = model  # injected (YOLO, mediapipe, etc.)

    def detect(self, frame) -> List[Tuple[int, int, int, int]]:
        """
        Returns list of bounding boxes for detected persons.
        """
        detections = self.detect_objects(frame)
        return [d["bbox"] for d in detections if d["class_id"] == 0]

    def detect_objects(self, frame, min_confidence: float = 0.3) -> List[Dict[str, Any]]:
        results = self.model(frame)
        detections: List[Dict[str, Any]] = []

        for r in results:
            for box in r.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0]) if hasattr(box, "conf") else 0.0
                if confidence < min_confidence:
                    continue

                bbox = tuple(map(int, box.xyxy[0]))
                detections.append(
                    {
                        "bbox": bbox,
                        "class_id": class_id,
                        "class_name": self._class_name(class_id),
                        "confidence": confidence,
                    }
                )

        return detections

    def _class_name(self, class_id: int) -> str:
        names = getattr(self.model, "names", None)
        if isinstance(names, dict):
            return str(names.get(class_id, class_id))
        if isinstance(names, list) and 0 <= class_id < len(names):
            return str(names[class_id])
        return str(class_id)
