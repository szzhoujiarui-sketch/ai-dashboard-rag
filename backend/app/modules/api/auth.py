from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthUser:
    def __init__(self, api_key: str, owner_id: str):
        self.api_key = api_key
        self.owner_id = owner_id


def verify_api_key(api_key_header: str = Security(API_KEY_HEADER)) -> AuthUser:
    owners = settings.get_api_key_owners()

    if owners:
        if not api_key_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少 API 密钥",
            )
        owner_id = owners.get(api_key_header)
        if owner_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的 API 密钥",
            )
        return AuthUser(api_key=api_key_header, owner_id=owner_id)

    app_api_key = settings.app_api_key
    if not app_api_key:
        return AuthUser(api_key="", owner_id="default")

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

    return AuthUser(api_key=api_key_header, owner_id="default")
