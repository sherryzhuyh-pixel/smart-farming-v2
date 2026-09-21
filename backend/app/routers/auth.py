"""Authentication API"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends

from app.auth import create_access_token, get_current_user
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["认证"])

# 从环境变量读取admin密码，未设置则使用默认
DEMO_USERS = None

def get_demo_users():
    global DEMO_USERS
    if DEMO_USERS is None:
        settings = get_settings()
        admin_pwd = settings.ADMIN_PASSWORD or "admin123"
        DEMO_USERS = {
            settings.ADMIN_USERNAME: {
                "user_id": 1,
                "username": settings.ADMIN_USERNAME,
                "role": "admin",
                "password": admin_pwd,
            },
            "field_manager": {"user_id": 2, "username": "field_manager", "role": "field_manager", "password": "fm123"},
        }
    return DEMO_USERS


@router.post("/login")
def login(credentials: dict):
    """User login - returns JWT token"""
    username = credentials.get("username")
    password = credentials.get("password")

    if not username or not password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username and password required")

    users = get_demo_users()
    user = users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    settings = get_settings()
    access_token = create_access_token(
        data={"sub": str(user["user_id"]), "username": user["username"], "role": user["role"]},
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {
        "code": 0,
        "message": "登录成功",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "user_id": user["user_id"],
                "username": user["username"],
                "role": user["role"],
            },
        },
    }


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
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
