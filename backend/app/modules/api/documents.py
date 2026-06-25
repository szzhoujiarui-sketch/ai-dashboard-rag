from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
import aiofiles
from datetime import datetime
from app.modules.rag.engine import RAGEngine
from app.modules.rag.document_registry import document_registry
from app.config import settings

ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.csv', '.json'}
router = APIRouter()

@router.post("/upload")
async def upload_document(request: Request, file: UploadFile = File(...)):
    rag_engine: RAGEngine = request.app.state.rag_engine
    file_size = 0
    original_filename = file.filename or "uploaded_file"
    ext = os.path.splitext(original_filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
    
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.upload_dir, safe_filename)
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > 10 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="文件大小超过限制")
                await f.write(chunk)
        
        result = await rag_engine.ingest_document(file_path)
        document_id = result.get("document_id")
        if document_id:
            document_registry.register(safe_filename, document_id)
        
        result["filename"] = original_filename
        return JSONResponse(content=result)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"处理文档失败: {str(e)}")

@router.get("/list")
async def list_documents():
    files = []
    if os.path.exists(settings.upload_dir):
        for f in os.listdir(settings.upload_dir):
            file_path = os.path.join(settings.upload_dir, f)
            files.append({
                "filename": f,
                "original_filename": document_registry.get_document_id(f) or f,
                "size": os.path.getsize(file_path),
                "modified": datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).isoformat()
            })
    return {"documents": files}

@router.delete("/{filename}")
async def delete_document(request: Request, filename: str):
    rag_engine: RAGEngine = request.app.state.rag_engine
    file_path = os.path.join(settings.upload_dir, filename)
    
    if os.path.exists(file_path):
        document_id = document_registry.get_document_id(filename)
        if document_id:
            await rag_engine.delete_document(document_id)
            document_registry.unregister(filename)
        
        os.remove(file_path)
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="文件不存在")
