import os
import sys
import logging
import contextlib
import io
import numpy as np
from typing import List, Dict, Optional
from utils.logger import logger


def _suppress_onnx_logging():
    logging.getLogger('onnxruntime').setLevel(logging.ERROR)
    logging.getLogger('insightface').setLevel(logging.ERROR)
    
    for name in ['onnx', 'onnxruntime', 'insightface', 'insightface.app', 
                 'insightface.model_zoo', 'insightface.utils']:
        logging.getLogger(name).setLevel(logging.ERROR)


class InsightFaceDetector:

    def __init__(self, model_name: str = "buffalo_l"):
        self.model_name = model_name
        self.app = None
        self._initialized = False
        self._using_cuda = False

    def _setup_cuda_paths(self):
        if sys.platform != "win32":
            return True
        
        cuda_base = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
        
        cuda_versions = ["v12.2", "v12.1", "v12.3", "v12.4", "v12.5", "v12.6", "v12.0", "v11.8", "v13.0"]
        
        for version in cuda_versions:
            cuda_path = os.path.join(cuda_base, version, "bin")
            if os.path.exists(cuda_path):
                logger.info(f"Found CUDA at: {cuda_path}")
                os.environ["PATH"] = cuda_path + os.pathsep + os.environ.get("PATH", "")
                try:
                    os.add_dll_directory(cuda_path)
                except Exception:
                    pass
                
                libnvvp_path = os.path.join(cuda_base, version, "libnvvp")
                if os.path.exists(libnvvp_path):
                    os.environ["PATH"] = libnvvp_path + os.pathsep + os.environ.get("PATH", "")
                    try:
                        os.add_dll_directory(libnvvp_path)
                    except Exception:
                        pass
                
                return True
        
        logger.warning("CUDA Toolkit not found")
        return False

    def initialize(self) -> bool:
        if self._initialized:
            logger.warning("InsightFace already initialized")
            return True

        try:
            self._setup_cuda_paths()
            
            logger.info("Importing InsightFace...")
            import insightface
            from insightface.app import FaceAnalysis
            logger.info(f"InsightFace version: {insightface.__version__}")

            import onnxruntime as ort
            available_providers = ort.get_available_providers()
            logger.info(f"Available ONNX providers: {available_providers}")

            if "CUDAExecutionProvider" in available_providers:
                providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
                logger.info("Using CUDA + CPU providers")
            else:
                providers = ["CPUExecutionProvider"]
                logger.warning("CUDA not available, using CPU only")

            logger.info(f"Loading InsightFace model: {self.model_name}")
            
            _suppress_onnx_logging()
            
            with contextlib.redirect_stdout(io.StringIO()), \
                 contextlib.redirect_stderr(io.StringIO()):
                self.app = FaceAnalysis(
                    name=self.model_name,
                    providers=providers,
                )
                self.app.prepare(ctx_id=0, det_size=(640, 640))

            actual_providers = []
            for model in self.app.models.values():
                if hasattr(model, 'session'):
                    actual_providers.extend(model.session.get_providers())
            
            self._using_cuda = "CUDAExecutionProvider" in actual_providers
            if self._using_cuda:
                logger.success(f"InsightFace initialized with CUDA ({self.model_name})")
            else:
                logger.warning(f"InsightFace initialized with CPU only ({self.model_name})")

            self._initialized = True
            return True

        except ImportError as e:
            logger.error(f"InsightFace import error: {e}")
            logger.error("Run: pip install insightface onnxruntime-gpu")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize InsightFace: {e}")
            import traceback
            traceback.print_exc()
            return False

    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        if not self._initialized:
            logger.error("InsightFace not initialized")
            return []

        if frame is None:
            return []

        try:
            faces = self.app.get(frame)

            detected = []
            for idx, face in enumerate(faces):
                bbox = face.bbox.astype(int)

                face_data = {
                    "face_id": idx,
                    "bbox": (int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])),
                    "embedding": face.embedding.astype(np.float32),
                    "det_score": float(face.det_score),
                }

                if hasattr(face, "kps") and face.kps is not None:
                    face_data["landmarks"] = face.kps

                detected.append(face_data)

            return detected

        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return []

    def get_embedding(self, frame: np.ndarray) -> Optional[np.ndarray]:
        faces = self.detect_faces(frame)
        if not faces:
            return None

        best_face = max(faces, key=lambda f: f["det_score"])
        return best_face["embedding"]

    def is_using_cuda(self) -> bool:
        return self._using_cuda

    def close(self):
        self.app = None
        self._initialized = False
        self._using_cuda = False

    def __del__(self):
        self.close()

    def __repr__(self):
        status = "CUDA" if self._using_cuda else "CPU"
        init_status = "initialized" if self._initialized else "not initialized"
        return f"InsightFaceDetector(model='{self.model_name}', {init_status}, {status})"
