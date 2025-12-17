"""
认证相关的 API 路由
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from app.utils.auth import get_user_by_username, verify_password, create_user
from app.utils.session_manager import create_session, get_session, delete_session

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


class LogoutRequest(BaseModel):
    session_id: str


class LoginResponse(BaseModel):
    session_id: str
    username: str
    is_admin: bool


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """
    用户登录
    
    返回 session_id，前端需要保存到 cookie 或 localStorage
    """
    # 获取用户信息
    user = get_user_by_username(request.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    
    # 验证密码（明文比较）
    if not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 创建 session
    ip_address = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")
    session_id = create_session(user["id"], ip_address, user_agent)
    
    return LoginResponse(
        session_id=session_id,
        username=user["username"],
        is_admin=user["is_admin"]
    )


@router.post("/register")
async def register(request: RegisterRequest):
    """
    用户注册
    """
    user_id = create_user(request.username, request.password, request.email)
    if not user_id:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    
    return {"message": "注册成功", "user_id": user_id}


@router.post("/logout")
async def logout(request: LogoutRequest):
    """
    登出（删除 session）
    """
    deleted = delete_session(request.session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session 不存在")
    return {"message": "登出成功"}


@router.get("/me")
async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """
    获取当前登录用户信息
    
    从 Authorization header 中获取 session_id（格式：Bearer {session_id}）
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="未登录")
    
    session_id = credentials.credentials
    if not session_id:
        raise HTTPException(status_code=401, detail="未登录")
    
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=401, detail="Session 无效或已过期")
    
    return {
        "user_id": session["user_id"],
        "username": session["username"],
        "is_admin": session["is_admin"],
        "is_active": session["is_active"]
    }
