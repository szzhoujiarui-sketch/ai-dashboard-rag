import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from ...config import settings

class MetricsCollector:
    def __init__(self):
        self.metrics_file = os.path.join(settings.chroma_persist_dir, "metrics.json")
        self.started_at = datetime.now()
        self._load()

    def _trim(self):
        cutoff = datetime.now() - timedelta(days=settings.query_history_retention_days)
        retained = []
        for query in self.query_history:
            timestamp = self._parse_timestamp(query.get("timestamp"))
            if timestamp and timestamp >= cutoff:
                retained.append(query)
        self.query_history = retained
        if len(self.query_history) > settings.max_query_history:
            self.query_history = self.query_history[-settings.max_query_history:]

    def _parse_timestamp(self, value):
        if not isinstance(value, str):
            return None
        try:
            timestamp = datetime.fromisoformat(value)
        except ValueError:
            return None
        if timestamp.tzinfo is not None:
            timestamp = timestamp.astimezone().replace(tzinfo=None)
        return timestamp

    def _load(self):
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                data = json.load(f)
                self.total_queries = data.get("total_queries", 0)
                self.total_documents = data.get("total_documents", 0)
                self.query_history = data.get("query_history", [])
            self._trim()
        else:
            self.total_queries = 0
            self.total_documents = 0
            self.query_history = []

    def _save(self):
        self._trim()
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
        with open(self.metrics_file, 'w') as f:
            json.dump({
                "total_queries": self.total_queries,
                "total_documents": self.total_documents,
                "query_history": self.query_history
            }, f, indent=2)

    def increment_queries(self, response_time: float):
        self.total_queries += 1
        self.query_history.append({
            "timestamp": datetime.now().isoformat(),
            "response_time": response_time
        })
        self._save()

    def increment_documents(self):
        self.total_documents += 1
        self._save()

    def _format_uptime(self) -> str:
        total_seconds = int((datetime.now() - self.started_at).total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}m"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def get_dashboard_stats(self) -> Dict[str, Any]:
        avg_response_time = 0.0
        if self.query_history:
            recent = self.query_history[-100:]
            avg_response_time = sum(q.get("response_time", 0.0) for q in recent) / len(recent)
        
        return {
            "total_queries": self.total_queries,
            "total_documents": self.total_documents,
            "uptime": self._format_uptime(),
            "avg_response_time": round(avg_response_time, 2),
            "last_updated": datetime.now().isoformat()
        }

    def get_query_trends(self) -> Dict[str, List]:
        days = 7
        data = []
        base_date = datetime.now() - timedelta(days=days - 1)
        
        for i in range(days):
            date = base_date + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            day_queries = [q for q in self.query_history if q["timestamp"].startswith(date_str)]
            data.append({
                "date": date_str,
                "queries": len(day_queries),
                "avg_response_time": round(
                    sum(q.get("response_time", 0.0) for q in day_queries) / len(day_queries),
                    2
                ) if day_queries else 0.0
            })
        
        return {
            "dates": [d["date"] for d in data],
            "queries": [d["queries"] for d in data],
            "avg_response_time": [d["avg_response_time"] for d in data]
        }
