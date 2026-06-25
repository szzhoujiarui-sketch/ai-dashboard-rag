import json
import os
from typing import Dict, Optional
from ...config import settings

REGISTRY_PATH = os.path.join(settings.chroma_persist_dir, "document_registry.json")

class DocumentRegistry:
    def __init__(self):
        self._mapping: Dict[str, str] = {}
        self._load()

    def _load(self):
        if os.path.exists(REGISTRY_PATH):
            with open(REGISTRY_PATH, 'r') as f:
                self._mapping = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(self._mapping, f, indent=2)

    def register(self, filename: str, document_id: str):
        self._mapping[filename] = document_id
        self._save()

    def get_document_id(self, filename: str) -> Optional[str]:
        return self._mapping.get(filename)

    def unregister(self, filename: str):
        self._mapping.pop(filename, None)
        self._save()

document_registry = DocumentRegistry()
