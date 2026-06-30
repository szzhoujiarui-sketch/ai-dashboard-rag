import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.modules.api.documents import get_upload_path
from app.modules.dashboard.metrics import MetricsCollector
from app.modules.rag.document_registry import DocumentRegistry


def test_health_check_returns_modules():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_empty_question_returns_bad_request():
    with TestClient(app) as client:
        response = client.post("/api/v1/chat/ask", json={"question": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "问题不能为空"


def test_upload_path_rejects_traversal():
    with pytest.raises(HTTPException) as exc:
        get_upload_path("../outside.txt")

    assert exc.value.status_code == 400


def test_document_registry_stores_display_metadata(tmp_path, monkeypatch):
    registry_path = tmp_path / "document_registry.json"
    monkeypatch.setattr("app.modules.rag.document_registry.REGISTRY_PATH", str(registry_path))

    registry = DocumentRegistry()
    registry.register("safe.txt", "doc-123", "original.txt", 12)

    entry = registry.get_document("safe.txt")
    assert registry.get_document_id("safe.txt") == "doc-123"
    assert entry["original_filename"] == "original.txt"
    assert entry["size"] == 12


def test_metrics_use_real_response_time(tmp_path):
    collector = MetricsCollector()
    collector.metrics_file = str(tmp_path / "metrics.json")
    collector.total_queries = 0
    collector.total_documents = 0
    collector.query_history = []

    collector.increment_queries(1.25)

    stats = collector.get_dashboard_stats()
    trends = collector.get_query_trends()

    assert stats["total_queries"] == 1
    assert stats["avg_response_time"] == 1.25
    assert "avg_accuracy" not in stats
    assert trends["avg_response_time"][-1] == 1.25


def test_app_api_keys_parsing(monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "app_api_keys", "key1:alice,key2:bob")
    owners = config.settings.get_api_key_owners()
    assert owners == {"key1": "alice", "key2": "bob"}


def test_app_api_keys_empty_when_unset(monkeypatch):
    from app import config
    monkeypatch.setattr(config.settings, "app_api_keys", "")
    owners = config.settings.get_api_key_owners()
    assert owners == {}


def test_verify_api_key_rejects_missing_header(monkeypatch):
    from app import config
    from app.modules.api.auth import verify_api_key
    monkeypatch.setattr(config.settings, "app_api_keys", "key1:alice")
    with pytest.raises(HTTPException) as exc:
        verify_api_key(x_api_key=None)
    assert exc.value.status_code == 401


def test_verify_api_key_rejects_invalid_key(monkeypatch):
    from app import config
    from app.modules.api.auth import verify_api_key
    monkeypatch.setattr(config.settings, "app_api_keys", "key1:alice")
    with pytest.raises(HTTPException) as exc:
        verify_api_key(x_api_key="wrong-key")
    assert exc.value.status_code == 401


def test_verify_api_key_returns_owner(monkeypatch):
    from app import config
    from app.modules.api.auth import verify_api_key
    monkeypatch.setattr(config.settings, "app_api_keys", "key1:alice")
    user = verify_api_key(x_api_key="key1")
    assert user.owner_id == "alice"


def test_verify_api_key_falls_back_to_default_when_no_keys(monkeypatch):
    from app import config
    from app.modules.api.auth import verify_api_key
    monkeypatch.setattr(config.settings, "app_api_keys", "")
    user = verify_api_key(x_api_key=None)
    assert user.owner_id == "default"


def test_document_registry_stores_owner_id(tmp_path, monkeypatch):
    registry_path = tmp_path / "document_registry.json"
    monkeypatch.setattr(
        "app.modules.rag.document_registry.REGISTRY_PATH", str(registry_path)
    )

    registry = DocumentRegistry()
    registry.register("a.txt", "doc-1", "a.txt", 10, owner_id="alice")
    registry.register("b.txt", "doc-2", "b.txt", 20, owner_id="bob")

    assert registry.get_owner("a.txt") == "alice"
    assert registry.get_owner("b.txt") == "bob"

    alice_docs = registry.get_documents_by_owner("alice")
    assert "a.txt" in alice_docs
    assert "b.txt" not in alice_docs


def test_delete_document_rejects_wrong_owner(tmp_path, monkeypatch):
    registry_path = tmp_path / "document_registry.json"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    monkeypatch.setattr(
        "app.modules.rag.document_registry.REGISTRY_PATH", str(registry_path)
    )
    from app import config
    monkeypatch.setattr(config.settings, "app_api_keys", "key-alice:alice,key-bob:bob")
    monkeypatch.setattr(config.settings, "upload_dir", str(upload_dir))

    from app.modules.rag.document_registry import document_registry

    file_path = upload_dir / "doc-alice.txt"
    file_path.write_text("alice content")
    document_registry._mapping = {}
    document_registry.register(
        "doc-alice.txt", "doc-1", "doc-alice.txt", 12, owner_id="alice"
    )

    with TestClient(app) as client:
        response = client.delete(
            "/api/v1/documents/doc-alice.txt",
            headers={"X-API-Key": "key-bob"},
        )

    assert response.status_code == 403
    assert "无权删除" in response.json()["detail"]
