import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

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


def test_chat_error_does_not_leak_internal_details():
    with TestClient(app) as client:
        mock_query = AsyncMock(side_effect=RuntimeError(
            "/app/chroma_db/internal-path api-key=sk-abc123"
        ))
        app.state.rag_engine.query = mock_query

        response = client.post("/api/v1/chat/ask", json={"question": "test"})

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
                "/api/v1/chat/ask", json={"question": "test"}
            )
        finally:
            app.state.rag_engine.query = original

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail == "查询失败"
    assert "/etc/passwd" not in detail
