import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("APP_API_KEY", "test-api-key-123")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.modules.api.documents import get_upload_path
from app.modules.dashboard.metrics import MetricsCollector
from app.modules.rag.document_registry import DocumentRegistry


AUTH_HEADER = {"X-API-Key": "test-api-key-123"}


def test_health_check_returns_modules():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_empty_question_returns_bad_request():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/ask",
            json={"question": "   "},
            headers=AUTH_HEADER,
        )

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




def test_chat_error_does_not_leak_internal_details():
    with TestClient(app) as client:
        mock_query = AsyncMock(side_effect=RuntimeError(
            "/app/chroma_db/internal-path api-key=sk-abc123"
        ))
        app.state.rag_engine.query = mock_query

        response = client.post(
            "/api/v1/chat/ask",
            json={"question": "test"},
            headers=AUTH_HEADER,
        )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail == "查询失败"
    assert "/app/chroma_db" not in detail
    assert "api-key" not in detail
    assert "sk-" not in detail
    assert "internal-path" not in detail


def test_upload_error_does_not_leak_internal_details():
    with TestClient(app) as client:
        mock_ingest = AsyncMock(side_effect=RuntimeError(
            "/app/uploads/secret-file.txt PyPDFLoader internal trace"
        ))
        app.state.rag_engine.ingest_document = mock_ingest

        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", b"hello world", "text/plain")},
            headers=AUTH_HEADER,
        )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail == "处理文档失败"
    assert "/app/uploads" not in detail
    assert "PyPDFLoader" not in detail
    assert "secret-file" not in detail


def test_unhandled_exception_returns_generic_error():
    with TestClient(app) as client:

        original = app.state.rag_engine.query
        try:

            async def crash(*args, **kwargs):
                raise ValueError("/etc/passwd sensitive info")
            app.state.rag_engine.query = crash

            response = client.post(
                "/api/v1/chat/ask",
                json={"question": "test"},
                headers=AUTH_HEADER,
            )
        finally:
            app.state.rag_engine.query = original

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail == "查询失败"
    assert "/etc/passwd" not in detail


def test_health_check_no_auth_required():
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200


def test_chat_rejects_without_api_key():
    with TestClient(app) as client:
        response = client.post("/api/v1/chat/ask", json={"question": "test"})

    assert response.status_code == 403


def test_chat_rejects_with_wrong_api_key():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/ask",
            json={"question": "test"},
            headers={"X-API-Key": "wrong-key"},
        )

    assert response.status_code == 403


def test_chat_accepts_valid_api_key():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/chat/ask",
            json={"question": "   "},
            headers=AUTH_HEADER,
        )

    assert response.status_code == 400


def test_documents_list_requires_auth():
    with TestClient(app) as client:
        response = client.get("/api/v1/documents/list")

    assert response.status_code == 403


def test_stats_dashboard_accepts_valid_api_key():
    with TestClient(app) as client:
        response = client.get("/api/v1/stats/dashboard", headers=AUTH_HEADER)

    assert response.status_code == 200


def test_query_history_capped_at_max(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "max_query_history", 5)

    collector = MetricsCollector()
    collector.metrics_file = str(tmp_path / "metrics.json")
    collector.total_queries = 0
    collector.total_documents = 0
    collector.query_history = []

    for i in range(10):
        collector.increment_queries(float(i))

    assert len(collector.query_history) == 5
    assert collector.query_history[0]["response_time"] == 5.0
    assert collector.query_history[-1]["response_time"] == 9.0


def test_query_history_removes_expired_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "query_history_retention_days", 7)

    collector = MetricsCollector()
    collector.metrics_file = str(tmp_path / "metrics.json")
    collector.total_queries = 0
    collector.total_documents = 0
    old_date = (datetime.now() - timedelta(days=10)).isoformat()
    recent_date = datetime.now().isoformat()
    collector.query_history = [
        {"timestamp": old_date, "response_time": 1.0},
        {"timestamp": recent_date, "response_time": 2.0},
    ]

    collector._trim()

    assert len(collector.query_history) == 1
    assert collector.query_history[0]["response_time"] == 2.0


def test_load_trims_oversized_metrics_file(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "max_query_history", 3)

    metrics_path = tmp_path / "metrics.json"

    oversized = {
        "total_queries": 100,
        "total_documents": 50,
        "query_history": [
            {"timestamp": datetime.now().isoformat(), "response_time": float(i)}
            for i in range(10)
        ],
    }
    with open(metrics_path, "w") as f:
        json.dump(oversized, f)

    collector = MetricsCollector()
    collector.metrics_file = str(metrics_path)
    collector._load()

    assert len(collector.query_history) == 3


def test_query_history_skips_invalid_timestamps(tmp_path):
    collector = MetricsCollector()
    collector.metrics_file = str(tmp_path / "metrics.json")
    collector.total_queries = 0
    collector.total_documents = 0
    collector.query_history = [
        {"timestamp": "not-a-date", "response_time": 1.0},
        {"response_time": 2.0},
        {"timestamp": datetime.now().isoformat(), "response_time": 3.0},
    ]

    collector._trim()

    assert len(collector.query_history) == 1
    assert collector.query_history[0]["response_time"] == 3.0


def test_query_history_accepts_timezone_aware_timestamps(tmp_path):
    collector = MetricsCollector()
    collector.metrics_file = str(tmp_path / "metrics.json")
    collector.total_queries = 0
    collector.total_documents = 0
    collector.query_history = [
        {"timestamp": datetime.now(timezone.utc).isoformat(), "response_time": 1.0},
    ]

    collector._trim()

    assert len(collector.query_history) == 1

def test_delete_nonexistent_file_returns_not_found():
    with TestClient(app) as client:
        response = client.delete("/api/v1/documents/nonexistent.txt", headers=AUTH_HEADER)

    assert response.status_code == 404
    assert response.json()["detail"] == "文件不存在"


def test_registry_save_is_atomic(tmp_path, monkeypatch):
    registry_path = tmp_path / "document_registry.json"
    monkeypatch.setattr("app.modules.rag.document_registry.REGISTRY_PATH", str(registry_path))

    registry = DocumentRegistry()
    registry.register("doc.txt", "doc-1", "original.txt", 100)

    assert os.path.exists(registry_path)
    data = json.loads(registry_path.read_text())
    assert data["doc.txt"]["document_id"] == "doc-1"

    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_concurrent_delete_same_file_is_safe(tmp_path, monkeypatch):
    registry_path = tmp_path / "document_registry.json"
    monkeypatch.setattr("app.modules.rag.document_registry.REGISTRY_PATH", str(registry_path))

    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    upload_dir.mkdir()
    test_file = upload_dir / "shared.txt"
    test_file.write_text("hello")

    registry = DocumentRegistry()
    registry.register("shared.txt", "doc-shared", "shared.txt", 5)
    monkeypatch.setattr("app.modules.api.documents.document_registry", registry)

    with TestClient(app) as client:

        async def safe_delete(document_id):
            return True
        app.state.rag_engine.delete_document = safe_delete

        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(
                    client.delete, "/api/v1/documents/shared.txt",
                    headers=AUTH_HEADER
                )
                for _ in range(2)
            ]
            results = [f.result() for f in futures]

    assert sorted(r.status_code for r in results) == [200, 404]
    assert any(r.json().get("status") == "deleted" for r in results)
    assert any(r.json().get("detail") == "文件不存在" for r in results)

    assert not test_file.exists()

    assert "shared.txt" not in registry._mapping


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


def test_verify_api_key_with_app_api_keys_rejects_missing_header(monkeypatch):
    from app import config
    from app.modules.api.auth import verify_api_key
    monkeypatch.setattr(config.settings, "app_api_keys", "key1:alice")
    with pytest.raises(HTTPException) as exc:
        verify_api_key(api_key_header=None)
    assert exc.value.status_code == 401


def test_verify_api_key_with_app_api_keys_returns_owner(monkeypatch):
    from app import config
    from app.modules.api.auth import verify_api_key
    monkeypatch.setattr(config.settings, "app_api_keys", "key1:alice")
    user = verify_api_key(api_key_header="key1")
    assert user.owner_id == "alice"


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

    monkeypatch.setattr("app.modules.rag.document_registry.REGISTRY_PATH", str(registry_path))
    monkeypatch.setattr(settings, "upload_dir", str(upload_dir))
    from app import config
    monkeypatch.setattr(config.settings, "app_api_keys", "key-alice:alice,key-bob:bob")

    from app.modules.rag.document_registry import document_registry

    file_path = upload_dir / "doc-alice.txt"
    file_path.write_text("alice content")
    document_registry._mapping = {}
    document_registry.register("doc-alice.txt", "doc-1", "doc-alice.txt", 12, owner_id="alice")

    with TestClient(app) as client:
        response = client.delete(
            "/api/v1/documents/doc-alice.txt",
            headers={"X-API-Key": "key-bob"},
        )

    assert response.status_code == 403
    assert "无权删除" in response.json()["detail"]


def test_chat_k_bounds_are_enforced():
    with TestClient(app) as client:
        response_zero = client.post(
            "/api/v1/chat/ask",
            json={"question": "hi", "k": 0},
            headers=AUTH_HEADER,
        )
        assert response_zero.status_code == 422

        response_oversized = client.post(
            "/api/v1/chat/ask",
            json={"question": "hi", "k": 101},
            headers=AUTH_HEADER,
        )
        assert response_oversized.status_code == 422
