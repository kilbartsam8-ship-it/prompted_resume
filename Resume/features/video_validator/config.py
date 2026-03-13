# features/video_validator/config.py

# =====================
# Video configuration
# =====================
FRAME_SAMPLE_FPS = 1
YOLO_MODEL_NAME = "yolov8n.pt"
MIN_PERSON_FRAMES_RATIO = 0.85
MAX_ALLOWED_PERSONS = 1
MAX_CENTER_OFFSET_RATIO = 0.25
MAX_MOVEMENT_STD = 0.15
OBJECT_CONFIDENCE_THRESHOLD = 0.35
UNWANTED_OBJECT_LABELS = {
    # Alcohol related
    "bottle",
    "wine glass",
    "cup",
    # Smoking related proxies available in COCO-like labels
    "cigarette",
    "cigar",
    "vape",
    "smoke",
    # Weapons / dangerous
    "knife",
    "gun",
    "pistol",
    "rifle",
}

# =====================
# Audio / Speech
# =====================
AUDIO_SAMPLE_RATE = 16_000
WHISPER_MODEL_NAME = "base"
MAX_TRANSCRIPT_CHARS = 20_000
TRANSCRIPT_CHUNK_SIZE = 512
TRANSCRIPT_CHUNK_OVERLAP = 50

# =====================
# Semantic matching
# =====================
EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"
SEMANTIC_SIMILARITY_THRESHOLD = 0.65
ENTITY_SIMILARITY_THRESHOLD = 0.70
SKILL_MATCH_MIN_COUNT = 2

# =====================
# Toxicity / Moderation
# =====================
TOXICITY_MODEL_NAMES = [
    "unitary/toxic-bert",
    "martin-ha/toxic-comment-model"
]

TOXICITY_PROB_THRESHOLD = 0.75
MAX_ALLOWED_TOXIC_SENTENCES = 0

# =====================
# System
# =====================
DEVICE = "cpu"       # or "cuda"
DTYPE = "float16"    # model loading preference
