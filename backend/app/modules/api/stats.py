from fastapi import APIRouter, Request
from app.modules.dashboard.metrics import MetricsCollector

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard_stats(request: Request):
    metrics_collector: MetricsCollector = request.app.state.metrics_collector
    return metrics_collector.get_dashboard_stats()

@router.get("/trends")
async def get_query_trends(request: Request):
    metrics_collector: MetricsCollector = request.app.state.metrics_collector
    return metrics_collector.get_query_trends()

@router.get("/health")
async def get_health():
    return {"status": "healthy", "version": "1.0.0"}
