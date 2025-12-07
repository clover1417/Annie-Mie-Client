import numpy as np
from typing import Optional, Dict, List
from identity.insightface_detector import InsightFaceDetector
from identity.identity_store import IdentityStore
from utils.logger import logger


class IdentityManager:

    def __init__(self):
        self.face_detector = InsightFaceDetector()
        self.identity_store = IdentityStore()
        self._initialized = False
        self._face_detection_available = False

    def initialize(self):
        if self._initialized:
            logger.warning("Identity manager already initialized")
            return

        logger.info("Initializing Identity Manager...")
        
        self._face_detection_available = self.face_detector.initialize()
        if self._face_detection_available:
            if self.face_detector.is_using_cuda():
                logger.success("Face detection enabled (CUDA)")
            else:
                logger.success("Face detection enabled (CPU)")
        else:
            logger.warning("Face detection unavailable")
        
        self.identity_store.initialize()
        self._initialized = True
        logger.success("Identity Manager initialized")

    def identify_faces(self, video_frame: Optional[np.ndarray], threshold: float = 0.6) -> Dict:
        result = {
            "detected_ids": [],
            "num_faces": 0,
            "new_ids": []
        }

        if video_frame is None:
            return result

        if not self._face_detection_available:
            return result

        try:
            faces = self.face_detector.detect_faces(video_frame)
            result["num_faces"] = len(faces)

            if not faces:
                return result

            for face in faces:
                embedding = face["embedding"]
                identity_id, is_new = self.identity_store.get_or_create_identity(embedding, threshold)
                result["detected_ids"].append(identity_id)
                if is_new:
                    result["new_ids"].append(identity_id)

            if len(result["detected_ids"]) == 1:
                logger.info(f"Face: {result['detected_ids'][0]}")
            else:
                logger.info(f"Faces: {result['detected_ids']}")

        except Exception as e:
            logger.error(f"Face detection error: {e}")

        return result

    def identify_speaker(self, video_frame: Optional[np.ndarray], threshold: float = 0.6) -> Dict:
        result = self.identify_faces(video_frame, threshold)
        
        legacy_result = {
            "identity_detected": len(result["detected_ids"]) > 0,
            "detected_ids": result["detected_ids"],
            "num_faces": result["num_faces"],
            "primary_id": result["detected_ids"][0] if result["detected_ids"] else None,
            "new_ids": result["new_ids"]
        }
        
        return legacy_result

    def get_all_identities(self) -> List[str]:
        return self.identity_store.get_all_identities()

    def is_face_detection_available(self) -> bool:
        return self._face_detection_available

    def close(self):
        self.face_detector.close()
        self._initialized = False
        self._face_detection_available = False
