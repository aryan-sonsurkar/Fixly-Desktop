from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.auth import CurrentUser as CurrentUser
from app.services.auth_service import AuthService

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> CurrentUser:
    token = credentials.credentials
    service = AuthService(access_token=token)
    try:
        user = await service.get_current_user(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return CurrentUser(
        id=user["id"],
        email=user.get("email", ""),
        profile=user.get("profile"),
        user_metadata=user.get("user_metadata"),
        access_token=token,
    )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> CurrentUser | None:
    if not credentials:
        return None
    token = credentials.credentials
    service = AuthService(access_token=token)
    try:
        user = await service.get_current_user(token)
    except Exception:
        return None
    return CurrentUser(
        id=user["id"],
        email=user.get("email", ""),
        profile=user.get("profile"),
        user_metadata=user.get("user_metadata"),
        access_token=token,
    )
