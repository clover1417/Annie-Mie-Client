import torch
import soundfile as sf
import librosa
import numpy as np
import os

from config import (
    SILERO_REPO,
    SILERO_MODEL,
    SILERO_THRESHOLD,
    SILERO_FORCE_RELOAD,
    SILERO_SAMPLE_RATE
)
from utils.logger import logger


class SpeechDetector:

    def __init__(self, threshold=None, device=None):
        self.model = None
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.threshold = threshold if threshold is not None else SILERO_THRESHOLD
        self.sample_rate = SILERO_SAMPLE_RATE
        self.get_speech_timestamps = None
        self._initialized = False

    def read_audio(self, path):
        audio_data, sr = sf.read(path)

        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        if sr != self.sample_rate:
            audio_data = librosa.resample(
                audio_data,
                orig_sr=sr,
                target_sr=self.sample_rate,
                res_type='soxr_hq'
            )

        waveform = torch.from_numpy(audio_data).float()

        return waveform

    def initialize(self):
        if self._initialized:
            logger.warning("Silero VAD already initialized, skipping...")
            return True

        logger.info("Loading Silero VAD (speech-only mode)...", prefix="🔄")

        self.model, utils = torch.hub.load(
            repo_or_dir=SILERO_REPO,
            model=SILERO_MODEL,
            force_reload=SILERO_FORCE_RELOAD,
            trust_repo=True
        )

        self.get_speech_timestamps = utils[0]
        self.model.to(self.device)
        self.model.eval()

        self._initialized = True
        logger.success(f"Silero VAD loaded successfully on {self.device}")
        return True

    def is_speech(self, audio_file):
        if not self._initialized:
            raise RuntimeError(
                "SpeechDetector not initialized. Call initialize() first."
            )

        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        wav = self.read_audio(audio_file)

        if len(wav) == 0:
            logger.warning(f"Empty audio file: {audio_file}")
            return False

        wav = wav.to(self.device)
        speech_timestamps = self.get_speech_timestamps(
            wav, self.model, threshold=self.threshold
        )

        return len(speech_timestamps) > 0

    def __del__(self):
        if self.device == 'cuda':
            torch.cuda.empty_cache()
        self.model = None
        self._initialized = False

    def __repr__(self):
        status = "initialized" if self._initialized else "not initialized"
        return (
            f"SpeechDetector(device='{self.device}', "
            f"threshold={self.threshold}, status='{status}')"
        )
