# Resume.features/video_validator/service.py

from typing import Dict, Any, List, Optional, Set, Tuple
import asyncio
import json
import tempfile
import shutil
import os
import copy
from pathlib import Path

from Resume.features.video_validator.config import (
    FRAME_SAMPLE_FPS,
    YOLO_MODEL_NAME,
    OBJECT_CONFIDENCE_THRESHOLD,
    UNWANTED_OBJECT_LABELS,
    AUDIO_SAMPLE_RATE,
    WHISPER_MODEL_NAME,
    DEVICE,
)
from Resume.features.video_validator.exceptions import (
    InputValidationError,
    VideoValidationError,
    AudioExtractionError,
    TranscriptionError,
    SemanticMatchingError,
    ModerationError,
    VideoExtractionError,
)

# Video modules
from Resume.features.video_validator.video.reader import VideoReader
from Resume.features.video_validator.video.frame_sampler import FrameSampler
from Resume.features.video_validator.video.person_detector import PersonDetector
from Resume.features.video_validator.video.motion_analyzer import MotionAnalyzer
from Resume.features.video_validator.video.center_analyzer import CenterAnalyzer
from Resume.features.video_validator.video.validator import VideoValidator

# Audio modules
from Resume.features.video_validator.audio.extractor import AudioExtractor
from Resume.features.video_validator.audio.resampler import AudioResampler
from Resume.features.video_validator.audio.transcriber import WhisperTranscriber
from Resume.features.video_validator.audio.validator import AudioValidator
from Resume.features.video_validator.audio.duration_analyzer import AudioDurationAnalyzer

# Semantic
from Resume.features.video_validator.semantics.embedder import TextEmbedder
from Resume.features.video_validator.semantics.matcher import SemanticMatcher
from Resume.features.video_validator.semantics.validator import SemanticValidator

# Moderation
from Resume.features.video_validator.moderation.detector import ToxicityDetector
from Resume.features.video_extraction.service import VideoExtractionService


class VideoValidationService:
    """
    Orchestrates the video validation pipeline.
    """

    def __init__(self, person_model: Optional[object] = None):
        # Video
        self.person_detector = self._build_person_detector(person_model)
        self.motion_analyzer = MotionAnalyzer()
        self.center_analyzer = CenterAnalyzer()
        self.video_validator = VideoValidator()

        # Audio
        self.audio_extractor = AudioExtractor()
        self.audio_resampler = AudioResampler()
        self.transcriber = WhisperTranscriber(
            model_name=WHISPER_MODEL_NAME,
            device=DEVICE,
        )
        self.audio_validator = AudioValidator()
        self.duration_analyzer = AudioDurationAnalyzer()

        # Moderation
        self.moderation = ToxicityDetector()

        # Video extraction (post validation)
        self.video_extractor = VideoExtractionService()

    def _build_person_detector(self, person_model: Optional[object]) -> Optional[PersonDetector]:
        if person_model is not None:
            return PersonDetector(person_model)

        try:
            from ultralytics import YOLO
        except Exception:
            return None

        try:
            model = YOLO(YOLO_MODEL_NAME)
            return PersonDetector(model)
        except Exception:
            return None

    async def validate_video_async(self, video_path: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(self.validate_video, video_path, resume_data)

    def validate_video(self, video_path: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the full validation pipeline.
        Always returns a structured result.
        Never raises raw exceptions outward.
        """

        results: Dict[str, Any] = {
            "video": None,
            "audio": None,
            "semantic": None,
            "moderation": None,
            "video_extraction": None,
            "resume_json": copy.deepcopy(resume_data) if resume_data else {},
            "final_valid": False,
            "errors": [],
        }

        try:
            self._validate_inputs(video_path, resume_data)
        except InputValidationError as e:
            results["errors"].append({"stage": "input", "error": str(e)})
            return results

        tmp_dir = tempfile.mkdtemp(prefix="video_validation_")

        try:
            # ----------------------------
            # 1) VIDEO STAGE
            # ----------------------------
            try:
                if self.person_detector is None:
                    results["video"] = {
                        "video_valid": False,
                        "reasons": ["Person detector model not configured"],
                        "total_frames": 0,
                        "frames_with_person": 0,
                        "multiple_person_frames": 0,
                        "frames_with_unwanted_objects": 0,
                        "unwanted_objects": [],
                        "unwanted_with_person": [],
                        "unwanted_in_surroundings": [],
                        "center_deviation_score": 1.0,
                        "movement_score": 0.0,
                    }
                else:
                    reader = VideoReader(video_path)
                    fps = reader.fps()
                    sampler = FrameSampler(fps=fps, sample_fps=FRAME_SAMPLE_FPS)

                    total_sampled = 0
                    frames_with_person = 0
                    multiple_person_frames = 0
                    centers = []
                    frames_with_unwanted_objects = 0
                    unwanted_labels: Set[str] = set()
                    unwanted_with_person: Set[str] = set()
                    unwanted_in_surroundings: Set[str] = set()
                    frame_width = 0
                    frame_height = 0

                    for _, frame in sampler.sample(reader.read_frames()):
                        total_sampled += 1
                        if frame is None:
                            continue
                        if frame_width == 0 or frame_height == 0:
                            frame_height, frame_width = frame.shape[:2]

                        detections = self.person_detector.detect_objects(
                            frame,
                            min_confidence=OBJECT_CONFIDENCE_THRESHOLD,
                        )
                        person_boxes = [d["bbox"] for d in detections if d["class_id"] == 0]

                        if person_boxes:
                            frames_with_person += 1
                            if len(person_boxes) > 1:
                                multiple_person_frames += 1
                            x1, y1, x2, y2 = person_boxes[0]
                            centers.append(((x1 + x2) // 2, (y1 + y2) // 2))

                        frame_has_unwanted = False
                        for detection in detections:
                            label = str(detection.get("class_name", "")).lower().strip()
                            if not self._is_unwanted_label(label):
                                continue

                            frame_has_unwanted = True
                            unwanted_labels.add(label)
                            obj_box = detection["bbox"]
                            if any(self._boxes_overlap(obj_box, person_box) for person_box in person_boxes):
                                unwanted_with_person.add(label)
                            else:
                                unwanted_in_surroundings.add(label)

                        if frame_has_unwanted:
                            frames_with_unwanted_objects += 1

                    reader.release()

                    center_score = self.center_analyzer.compute(
                        centers=centers,
                        frame_width=frame_width or 1,
                        frame_height=frame_height or 1,
                    )
                    movement_score = self.motion_analyzer.compute(centers=centers)

                    video_result = self.video_validator.validate(
                        total_frames=total_sampled,
                        frames_with_person=frames_with_person,
                        multiple_person_frames=multiple_person_frames,
                        unwanted_object_frames=frames_with_unwanted_objects,
                        unwanted_objects=sorted(unwanted_labels),
                        center_score=center_score,
                        movement_score=movement_score,
                    )

                    results["video"] = {
                        "video_valid": video_result.is_valid,
                        "reasons": video_result.reasons,
                        "total_frames": video_result.total_frames,
                        "frames_with_person": video_result.frames_with_person,
                        "multiple_person_frames": video_result.multiple_person_frames,
                        "frames_with_unwanted_objects": video_result.frames_with_unwanted_objects,
                        "unwanted_objects": video_result.unwanted_objects,
                        "unwanted_with_person": sorted(unwanted_with_person),
                        "unwanted_in_surroundings": sorted(unwanted_in_surroundings),
                        "center_deviation_score": video_result.center_deviation_score,
                        "movement_score": video_result.movement_score,
                    }

            except Exception as e:
                raise VideoValidationError(str(e))

            # ----------------------------
            # 2) AUDIO STAGE
            # ----------------------------
            try:
                raw_wav = os.path.join(tmp_dir, "audio_raw.wav")
                wav_path = os.path.join(tmp_dir, "audio_16k.wav")

                self.audio_extractor.extract(video_path, raw_wav)
                self.audio_resampler.resample(raw_wav, wav_path, AUDIO_SAMPLE_RATE)

                try:
                    transcript, language = self.transcriber.transcribe(wav_path)
                except Exception as e:
                    raise TranscriptionError(str(e))

                duration_seconds = self.duration_analyzer.compute(wav_path)

                audio_result = self.audio_validator.validate(
                    transcript=transcript,
                    duration_seconds=duration_seconds,
                    language=language,
                )

                results["audio"] = {
                    "transcript": audio_result.transcript,
                    "language": audio_result.language,
                    "duration_seconds": audio_result.duration_seconds,
                    "audio_valid": audio_result.is_valid,
                    "reasons": audio_result.reasons,
                }

            except Exception as e:
                if isinstance(e, TranscriptionError):
                    raise
                raise AudioExtractionError(str(e))

            # ----------------------------
            # 3) SEMANTIC STAGE
            # ----------------------------
            try:
                if not resume_data:
                    results["semantic"] = {
                        "semantic_valid": True,
                        "similarity": None,
                        "confidence": None,
                        "reasons": ["No resume data provided; semantic check skipped"],
                    }
                else:
                    resume_text = json.dumps(resume_data, ensure_ascii=False)
                    transcript = results["audio"]["transcript"]

                    embedder = TextEmbedder()
                    matcher = SemanticMatcher(embedder)
                    validator = SemanticValidator(matcher)
                    semantic_result = validator.validate(resume_text, transcript)

                    results["semantic"] = {
                        "semantic_valid": semantic_result.score.is_match,
                        "similarity": semantic_result.score.similarity,
                        "confidence": semantic_result.score.confidence,
                        "reasons": semantic_result.reasons,
                    }

            except Exception as e:
                raise SemanticMatchingError(str(e))

            # ----------------------------
            # 4) MODERATION STAGE
            # ----------------------------
            try:
                moderation_result = self.moderation.detect(results["audio"]["transcript"])
                results["moderation"] = {
                    "is_allowed": moderation_result.is_allowed,
                    "severity": moderation_result.severity,
                    "categories": moderation_result.categories,
                    "reasons": moderation_result.reasons,
                }

            except Exception as e:
                raise ModerationError(str(e))

            # ----------------------------
            # 5) FINAL DECISION
            # ----------------------------
            results["final_valid"] = (
                results["video"]["video_valid"]
                and results["audio"]["audio_valid"]
                and results["semantic"]["semantic_valid"]
                and results["moderation"]["is_allowed"]
            )

            # ----------------------------
            # 6) VIDEO EXTRACTION (only if approved)
            # ----------------------------
            try:
                if results["final_valid"]:
                    transcript = results["audio"].get("transcript", "")
                    video_summary = self.video_extractor.extract_professional_summary(transcript)
                    results["resume_json"]["video_summary"] = video_summary
                    results["video_extraction"] = {
                        "applied": True,
                        "video_summary": video_summary,
                        "reasons": [],
                    }
                else:
                    results["video_extraction"] = {
                        "applied": False,
                        "video_summary": "",
                        "reasons": ["Video not approved; extraction skipped"],
                    }
            except Exception as e:
                raise VideoExtractionError(str(e))

        except VideoValidationError as e:
            results["errors"].append({"stage": "video", "error": str(e)})

        except AudioExtractionError as e:
            results["errors"].append({"stage": "audio", "error": str(e)})

        except TranscriptionError as e:
            results["errors"].append({"stage": "transcription", "error": str(e)})

        except SemanticMatchingError as e:
            results["errors"].append({"stage": "semantic", "error": str(e)})

        except ModerationError as e:
            results["errors"].append({"stage": "moderation", "error": str(e)})

        except VideoExtractionError as e:
            results["errors"].append({"stage": "video_extraction", "error": str(e)})

        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

        return results

    @staticmethod
    def _validate_inputs(video_path: str, resume_data: Dict[str, Any]):
        if not isinstance(video_path, str) or not video_path.strip():
            raise InputValidationError("video_path must be a non-empty string.")

        path = Path(video_path)
        if not path.exists() or not path.is_file():
            raise InputValidationError(f"Video file not found: {video_path}")
        if path.stat().st_size == 0:
            raise InputValidationError(f"Video file is empty: {video_path}")

        if resume_data is None:
            return
        if not isinstance(resume_data, dict):
            raise InputValidationError("resume_data must be a dictionary.")

    @staticmethod
    def _is_unwanted_label(label: str) -> bool:
        if not label:
            return False
        normalized = label.lower()
        return normalized in UNWANTED_OBJECT_LABELS

    @staticmethod
    def _boxes_overlap(box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> bool:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        inter_w = max(0, min(ax2, bx2) - max(ax1, bx1))
        inter_h = max(0, min(ay2, by2) - max(ay1, by1))
        return inter_w > 0 and inter_h > 0
