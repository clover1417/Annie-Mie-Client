import torch
import soundfile as sf
import librosa
import numpy as np
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
from typing import Optional
from utils.logger import logger


class SemanticRecognition:

    def __init__(self):
        self.model = None
        self.feature_extractor = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model_name = "sanchit-gandhi/whisper-medium-fleurs-lang-id"
        self._initialized = False

    def initialize(self):
        if self._initialized:
            logger.warning("Semantic recognition already initialized")
            return

        logger.info("Loading Pipecat Smart Turn model...")

        try:
            self.feature_extractor = AutoFeatureExtractor.from_pretrained(self.model_name)
            self.model = AutoModelForAudioClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()

            self._initialized = True
            logger.success(f"Semantic recognition initialized on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load semantic model: {e}")
            logger.info("Semantic recognition will be disabled")

    def is_turn_complete(self, audio_path: str) -> bool:
        if not self._initialized:
            logger.warning("Semantic recognition not initialized, defaulting to True")
            return True

        try:
            # Load audio using soundfile
            audio_data, sample_rate = sf.read(audio_path)

            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)

            # Resample if needed using librosa with high quality
            if sample_rate != 16000:
                audio_data = librosa.resample(
                    audio_data,
                    orig_sr=sample_rate,
                    target_sr=16000,
                    res_type='soxr_hq'  # High quality resampling
                )

            waveform_np = audio_data

            inputs = self.feature_extractor(
                waveform_np,
                sampling_rate=16000,
                return_tensors="pt"
            )

            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits

            probabilities = torch.softmax(logits, dim=-1)
            max_prob = probabilities.max().item()

            turn_complete = max_prob > 0.7

            logger.info(f"Semantic turn detection: {'complete' if turn_complete else 'incomplete'} (confidence: {max_prob:.2f})")

            return turn_complete

        except Exception as e:
            logger.error(f"Error in semantic recognition: {e}")
            return True
