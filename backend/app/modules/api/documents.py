from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
import os
import uuid
import aiofiles
from datetime import datetime
from app.modules.rag.engine import RAGEngine
from app.modules.rag.document_registry import document_registry
from app.modules.api.auth import AuthUser, verify_api_key
from app.config import settings

ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.csv', '.json'}
router = APIRouter()

def get_upload_path(filename: str) -> str:
    upload_dir = os.path.abspath(settings.upload_dir)
    file_path = os.path.abspath(os.path.join(upload_dir, filename))
    if os.path.commonpath([upload_dir, file_path]) != upload_dir:
        raise HTTPException(status_code=400, detail="文件路径无效")
    return file_path

@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    auth_user: AuthUser = Depends(verify_api_key),
):
    rag_engine: RAGEngine = request.app.state.rag_engine
    file_size = 0
    original_filename = file.filename or "uploaded_file"
    ext = os.path.splitext(original_filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
    
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = get_upload_path(safe_filename)
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > 10 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="文件大小超过限制")
                await f.write(chunk)
        
        result = await rag_engine.ingest_document(file_path, owner_id=auth_user.owner_id)
        document_id = result.get("document_id")
        if document_id:
            document_registry.register(
                safe_filename, document_id, original_filename, file_size,
                owner_id=auth_user.owner_id,
            )
        
        result["filename"] = safe_filename
        result["original_filename"] = original_filename
        return JSONResponse(content=result)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"处理文档失败: {str(e)}")

@router.get("/list")
async def list_documents(auth_user: AuthUser = Depends(verify_api_key)):
    files = []
    owner_docs = document_registry.get_documents_by_owner(auth_user.owner_id)
    for filename in owner_docs:
        file_path = get_upload_path(filename)
        if not os.path.isfile(file_path):
            continue
        document = owner_docs[filename]
        files.append({
            "filename": filename,
            "safe_filename": filename,
            "original_filename": document.get("original_filename") or filename,
            "document_id": document.get("document_id"),
            "size": os.path.getsize(file_path),
            "modified": datetime.fromtimestamp(
                os.path.getmtime(file_path)
            ).isoformat()
        })
    return {"documents": files}

@router.delete("/{filename}")
async def delete_document(
    request: Request,
    filename: str,
    auth_user: AuthUser = Depends(verify_api_key),
):
    rag_engine: RAGEngine = request.app.state.rag_engine
    file_path = get_upload_path(filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    owner = document_registry.get_owner(filename)
    if owner is None or owner != auth_user.owner_id:
        raise HTTPException(status_code=403, detail="无权删除此文件")

    document_id = document_registry.get_document_id(filename)
    if document_id:
        await rag_engine.delete_document(document_id)
        document_registry.unregister(filename)

    os.remove(file_path)
    return {"status": "deleted", "filename": filename}
