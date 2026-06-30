from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.modules.rag.engine import RAGEngine
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    k: int = 4

class ChatResponse(BaseModel):
    answer: str
    sources: list

@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: Request, req: ChatRequest):
    rag_engine: RAGEngine = request.app.state.rag_engine
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    try:
        result = await rag_engine.query(req.question, req.k)
        return ChatResponse(**result)
    except Exception:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail="查询失败")

@router.get("/history")
async def get_chat_history():
    return {"history": []}
