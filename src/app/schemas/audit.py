from datetime import datetime

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    id: int
    actor_user_id: int
    workspace_id: int
    entity_type: str
    entity_id: int
    action: str
    changes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogQuery(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
