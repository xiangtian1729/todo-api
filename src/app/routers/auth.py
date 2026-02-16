"""
认证路由模块

提供两个端点：
    POST /auth/register  — 用户注册
    POST /auth/login     — 用户登录（返回 JWT token）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.user import Token, UserCreate, UserResponse
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


# ========== POST /auth/register — 用户注册 ==========
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """注册新用户

    流程：
        1. 检查用户名是否已存在
        2. 把密码哈希后存储（永远不存明文密码）
        3. 返回用户信息（不包含密码）
    """
    # 检查用户名是否已被注册
    query = select(User).where(User.username == user_in.username)
    result = await db.execute(query)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )

    # 创建用户（密码哈希后存储）
    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        # 并发场景下，两个请求都通过了“预检查”时，唯一索引仍是最终防线
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )
    await db.refresh(user)

    return user


# ========== POST /auth/login — 用户登录 ==========
@router.post(
    "/login",
    response_model=Token,
    summary="用户登录",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """用户登录，返回 JWT token

    为什么用 OAuth2PasswordRequestForm？
        这是 OAuth2 标准的登录表单格式，使用 username + password 字段。
        FastAPI 的 Swagger UI 会自动生成一个登录弹窗来测试。

    流程：
        1. 查找用户
        2. 验证密码
        3. 生成并返回 JWT token
    """
    # 查找用户
    query = select(User).where(User.username == form_data.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    # 验证用户存在且密码正确
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成 JWT token
    token = create_access_token(user.id)

    return {"access_token": token, "token_type": "bearer"}


# ========== GET /auth/me — 获取当前用户信息 ==========
@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的详细信息"""
    return current_user
