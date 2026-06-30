from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key_header: str = Security(API_KEY_HEADER)) -> str:
    app_api_key = settings.app_api_key
    if not app_api_key:
        return ""

    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="缺少 API 密钥",
        )

    if api_key_header != app_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的 API 密钥",
        )

    return api_key_header
