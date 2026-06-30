import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from ...config import settings

REGISTRY_PATH = os.path.join(settings.chroma_persist_dir, "document_registry.json")

class DocumentRegistry:
    def __init__(self):
        self._mapping: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if os.path.exists(REGISTRY_PATH):
            with open(REGISTRY_PATH, 'r') as f:
                self._mapping = json.load(f)
            for filename, value in list(self._mapping.items()):
                if isinstance(value, str):
                    self._mapping[filename] = {
                        "document_id": value,
                        "original_filename": filename,
                        "size": None,
                        "uploaded_at": None,
                    }

    def _save(self):
        os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
        with open(REGISTRY_PATH, 'w') as f:
            json.dump(self._mapping, f, indent=2)

    def register(self, filename: str, document_id: str, original_filename: str, size: int, owner_id: str = "default"):
        self._mapping[filename] = {
            "document_id": document_id,
            "original_filename": original_filename,
            "size": size,
            "uploaded_at": datetime.now().isoformat(),
            "owner_id": owner_id,
        }
        self._save()

    def get_document_id(self, filename: str) -> Optional[str]:
        entry = self._mapping.get(filename)
        return entry.get("document_id") if entry else None

    def get_document(self, filename: str) -> Optional[Dict[str, Any]]:
        return self._mapping.get(filename)

    def get_documents_by_owner(self, owner_id: str) -> Dict[str, Dict[str, Any]]:
        return {
            filename: entry
            for filename, entry in self._mapping.items()
            if entry.get("owner_id") == owner_id
        }

    def get_owner(self, filename: str) -> Optional[str]:
        entry = self._mapping.get(filename)
        return entry.get("owner_id") if entry else None

    def unregister(self, filename: str):
        self._mapping.pop(filename, None)
        self._save()

document_registry = DocumentRegistry()
