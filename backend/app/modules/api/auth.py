from fastapi import Header, HTTPException, status
from typing import Optional

from ...config import settings


class AuthUser:
    def __init__(self, api_key: str, owner_id: str):
        self.api_key = api_key
        self.owner_id = owner_id


def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> AuthUser:
    owners = settings.get_api_key_owners()
    if not owners:
        return AuthUser(api_key="", owner_id="default")

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 X-API-Key 请求头",
        )

    owner_id = owners.get(x_api_key)
    if owner_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 API Key",
        )

    return AuthUser(api_key=x_api_key, owner_id=owner_id)
