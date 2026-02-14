"""
用户相关的数据验证模型
"""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """注册时的请求格式"""

    username: str = Field(
        ..., min_length=3, max_length=50,
        examples=["alice"],
        description="用户名（3-50 个字符）",
    )
    password: str = Field(
        ..., min_length=6, max_length=100,
        examples=["123456"],
        description="密码（至少 6 个字符）",
    )


class UserResponse(BaseModel):
    """返回给用户的信息（不包含密码！）"""

    id: int
    username: str

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """登录成功后返回的 Token"""

    access_token: str
    token_type: str = "bearer"
