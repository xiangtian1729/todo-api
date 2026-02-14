"""
安全模块：密码哈希 + JWT Token

1. 密码安全：
   用户的密码绝对不能以明文存储。
   用 bcrypt 算法把密码"哈希"成乱码再存储，即使数据库泄露也无法反推原始密码。

2. JWT Token（JSON Web Token）：
   登录成功后生成"通行证"（token），之后每次请求带上它来证明身份。
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User

# ========== 密码哈希工具 ==========

def hash_password(password: str) -> str:
    """把明文密码转换为哈希值（用于注册时存储）"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否正确（用于登录时比对）"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ========== JWT Token 工具 ==========
# OAuth2PasswordBearer 告诉 FastAPI：
# "用户的 token 从请求头 Authorization: Bearer <token> 中获取"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    """创建 JWT token，包含用户 ID 和过期时间"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


# ========== 获取当前用户（依赖注入） ==========
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 token 中解析当前用户

    FastAPI 自动从请求头提取 token → 解码 → 查找用户 → 返回
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await db.get(User, int(user_id))
    if user is None:
        raise credentials_exception

    return user
