from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RoleEnum(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    role: RoleEnum

    model_config = {"from_attributes": True}


class WorkspaceMemberCreate(BaseModel):
    user_id: int = Field(gt=0)
    role: RoleEnum = RoleEnum.member


class WorkspaceMemberUpdate(BaseModel):
    role: RoleEnum


class WorkspaceMemberResponse(BaseModel):
    user_id: int
    username: str | None = None
    role: RoleEnum
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
