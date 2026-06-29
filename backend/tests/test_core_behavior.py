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
