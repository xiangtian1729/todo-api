from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: int
    workspace_id: int
    task_id: int
    author_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    tag: str = Field(min_length=1, max_length=50)


class TagResponse(BaseModel):
    id: int
    task_id: int
    tag: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WatcherCreate(BaseModel):
    user_id: int = Field(gt=0)


class WatcherResponse(BaseModel):
    id: int
    task_id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
