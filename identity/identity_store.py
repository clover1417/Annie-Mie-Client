import os
import json
import uuid
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from utils.logger import logger


class IdentityStore:
    
    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = Path(__file__).parent.parent / "data" / "identities"
        self.storage_path = Path(storage_path)
        self.identities_file = self.storage_path / "identities.json"
        self.embeddings_file = self.storage_path / "embeddings.npy"
        self.identities: Dict[str, Dict] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._load()
        self._initialized = True
        logger.success(f"Identity store initialized ({len(self.identities)} identities)")

    def _load(self):
        if self.identities_file.exists():
            with open(self.identities_file, 'r', encoding='utf-8') as f:
                self.identities = json.load(f)
        
        if self.embeddings_file.exists():
            data = np.load(self.embeddings_file, allow_pickle=True).item()
            self.embeddings = {k: np.array(v, dtype=np.float32) for k, v in data.items()}

    def _save(self):
        with open(self.identities_file, 'w', encoding='utf-8') as f:
            json.dump(self.identities, f, indent=2, ensure_ascii=False)
        
        if self.embeddings:
            np.save(self.embeddings_file, self.embeddings)

    def _cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(emb1, emb2) / (norm1 * norm2))

    def find_identity(self, face_embedding: np.ndarray, threshold: float = 0.6) -> Optional[str]:
        if not self.embeddings:
            return None
        
        best_id = None
        best_score = threshold
        
        for identity_id, stored_emb in self.embeddings.items():
            score = self._cosine_similarity(face_embedding, stored_emb)
            if score > best_score:
                best_score = score
                best_id = identity_id
        
        return best_id

    def create_identity(self, face_embedding: np.ndarray) -> str:
        identity_id = f"id-{uuid.uuid4().hex[:8]}"
        
        self.identities[identity_id] = {
            "id": identity_id,
            "name": None,
            "created_at": str(np.datetime64('now'))
        }
        self.embeddings[identity_id] = face_embedding.astype(np.float32)
        
        self._save()
        logger.info(f"Created new identity: {identity_id}")
        return identity_id

    def get_or_create_identity(self, face_embedding: np.ndarray, threshold: float = 0.6) -> Tuple[str, bool]:
        existing_id = self.find_identity(face_embedding, threshold)
        
        if existing_id:
            return existing_id, False
        
        new_id = self.create_identity(face_embedding)
        return new_id, True

    def update_embedding(self, identity_id: str, new_embedding: np.ndarray):
        if identity_id in self.identities:
            self.embeddings[identity_id] = new_embedding.astype(np.float32)
            self._save()

    def get_all_identities(self) -> List[str]:
        return list(self.identities.keys())

    def get_identity_info(self, identity_id: str) -> Optional[Dict]:
        return self.identities.get(identity_id)
