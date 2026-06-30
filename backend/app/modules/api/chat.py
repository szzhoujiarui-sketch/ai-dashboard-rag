from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from app.modules.rag.engine import RAGEngine
from app.modules.api.auth import AuthUser, verify_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    k: int = Field(default=4, ge=1, le=100)

class ChatResponse(BaseModel):
    answer: str
    sources: list

@router.post("/ask", response_model=ChatResponse)
async def ask_question(
    request: Request,
    req: ChatRequest,
    auth_user: AuthUser = Depends(verify_api_key),
):
    rag_engine: RAGEngine = request.app.state.rag_engine
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    
    try:
        result = await rag_engine.query(req.question, req.k, owner_id=auth_user.owner_id)
        return ChatResponse(**result)
    except Exception:
        logger.exception("RAG query failed")
        raise HTTPException(status_code=500, detail="查询失败")

@router.get("/history")
async def get_chat_history(auth_user: AuthUser = Depends(verify_api_key)):
    return {"history": []}
