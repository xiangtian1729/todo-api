from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    blocked = "blocked"
    done = "done"


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"


class TaskSortBy(str, Enum):
    created_at = "created_at"
    updated_at = "updated_at"
    due_at = "due_at"
    status = "status"
    id = "id"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    assignee_id: int | None = Field(default=None, gt=0)
    due_at: datetime | None = None


class TaskUpdate(BaseModel):
    version: int = Field(ge=1)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    assignee_id: int | None = Field(default=None, gt=0)
    due_at: datetime | None = None


class TaskStatusTransition(BaseModel):
    to_status: TaskStatus


class TaskResponse(BaseModel):
    id: int
    workspace_id: int
    project_id: int
    title: str
    description: str | None
    status: TaskStatus
    creator_id: int
    assignee_id: int | None
    due_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
