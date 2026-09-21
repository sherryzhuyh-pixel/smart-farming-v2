"""Authentication API (Feishu Base version)"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Request

from app.auth import AuthService, get_password_hash, get_current_user
from app.repositories import get_repositories, RepositoryFactory
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login")
async def login(
    credentials: dict,
    repos: RepositoryFactory = Depends(get_repositories),
):
    """User login - returns JWT token"""
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username and password required",
        )

    auth_service = AuthService(repos.users)
    user = await auth_service.authenticate(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 更新最后登录时间
    try:
        await repos.users.update_by_pk(
            username,
            {"last_login": datetime.now(timezone.utc).isoformat()},
        )
    except Exception:
        # 登录成功但更新 last_login 失败不影响主流程
        pass

    access_token = auth_service.create_access_token(
        username, user.get("role", "operator")
    )
    settings = get_settings()
    return {
        "code": 0,
        "message": "登录成功",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user.get("_record_id"),
                "username": user.get("username"),
                "role": user.get("role"),
            },
        },
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "code": 0,
        "message": "success",
        "data": {
            "user_id": current_user.get("sub"),
            "username": current_user.get("username"),
            "role": current_user.get("role"),
        },
    }
