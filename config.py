import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SERVER_URI = os.getenv("SERVER_URI", "ws://localhost:8765")

BASE_DIR = Path(__file__).parent
TEMP_RECORDINGS_DIR = Path(tempfile.gettempdir()) / "annie_mie_recordings"
os.makedirs(TEMP_RECORDINGS_DIR, exist_ok=True)
OUT_DIR = str(TEMP_RECORDINGS_DIR)

RATE = 16000
CHUNK_SIZE = 512
AUDIO_FORMAT = "flac"
FLAC_COMPRESSION = 5

SPIKE_FACTOR = 2.5
STOP_FACTOR = 2.5
RELEASE_RATIO = 0.25
SILENCE_LIMIT = 2.0
SILENCE_ABS = 0.008
MIN_RECORD_SECONDS = 0.3
BACKGROUND_ALPHA = 0.95

VIDEO_ENABLED = True
CAMERA_INDEX = 0
VIDEO_FPS = 60.0
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
JPEG_QUALITY = 75
BUFFER_DURATION = 30.0

DEBUG_MESSAGE_STATS = True

SILERO_REPO = "snakers4/silero-vad"
SILERO_MODEL = "silero_vad"
SILERO_THRESHOLD = 0.5
SILERO_FORCE_RELOAD = False
SILERO_SAMPLE_RATE = 16000

LLM_BUSY_FLAG = BASE_DIR / ".llm_busy"


def get_recorder_config():
    return {
        "target_sample_rate": float(RATE),
        "chunk_size": float(CHUNK_SIZE),
        "audio_format": AUDIO_FORMAT,
        "flac_compression": float(FLAC_COMPRESSION),
        "spike_factor": float(SPIKE_FACTOR),
        "stop_factor": float(STOP_FACTOR),
        "release_ratio": float(RELEASE_RATIO),
        "silence_limit_secs": float(SILENCE_LIMIT),
        "silence_abs_threshold": float(SILENCE_ABS),
        "min_record_seconds": float(MIN_RECORD_SECONDS),
        "background_alpha": float(BACKGROUND_ALPHA),
        "output_directory": OUT_DIR,
        "video_enabled": VIDEO_ENABLED,
        "camera_index": float(CAMERA_INDEX),
        "video_fps": float(VIDEO_FPS),
        "video_width": float(VIDEO_WIDTH),
        "video_height": float(VIDEO_HEIGHT),
        "jpeg_quality": float(JPEG_QUALITY),
        "buffer_duration_secs": float(BUFFER_DURATION),
    }


class MessageType:
    AUDIO = "audio"
    TEXT = "text"
    STATUS = "status"
    STATS = "stats"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"


class StatusType:
    GENERATING = "generating"
    DONE = "done"


class StatsType:
    FIRST_TOKEN = "first_token"
    COMPLETE = "complete"





