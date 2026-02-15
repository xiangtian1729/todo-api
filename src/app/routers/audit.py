from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogResponse
from app.schemas.common import PageResponse
from app.schemas.workspace import RoleEnum
from app.security import get_current_user
from app.services.audit import list_workspace_audit_logs
from app.services.permissions import require_workspace_role

router = APIRouter(tags=["Audit"])


@router.get(
    "/workspaces/{workspace_id}/audit-logs",
    response_model=PageResponse[AuditLogResponse],
)
async def get_audit_logs(
    workspace_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await require_workspace_role(
        db,
        workspace_id,
        current_user.id,
        allowed_roles={RoleEnum.owner.value, RoleEnum.admin.value},
    )
    items, total = await list_workspace_audit_logs(
        db,
        workspace_id=workspace_id,
        skip=skip,
        limit=limit,
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}
