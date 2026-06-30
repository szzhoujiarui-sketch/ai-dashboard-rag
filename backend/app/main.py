from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from app.modules.api import documents, chat, stats
from app.modules.rag.engine import RAGEngine
from app.modules.dashboard.metrics import MetricsCollector
from app.config import settings

load_dotenv()

rag_engine = RAGEngine()
metrics_collector = MetricsCollector()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rag_engine.initialize()
    app.state.rag_engine = rag_engine
    app.state.metrics_collector = metrics_collector
    yield
    await rag_engine.cleanup()

app = FastAPI(
    title="AI Dashboard + RAG MVP",
    description="模块化 AI 仪表盘与 RAG 问答系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(stats.router, prefix="/api/v1/stats", tags=["stats"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "modules": ["rag", "dashboard", "chat"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
