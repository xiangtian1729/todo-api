import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

SENSITIVE_FIELDS = {
    "password",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "authorization",
}


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_FIELDS:
                safe[key] = "***"
            else:
                safe[key] = _sanitize(item)
        return safe
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _serialize_changes(changes: dict[str, Any] | None) -> str | None:
    if not changes:
        return None
    safe_changes = _sanitize(changes)
    return json.dumps(safe_changes, default=str)


async def log_action(
    db: AsyncSession,
    *,
    actor_user_id: int,
    workspace_id: int,
    entity_type: str,
    entity_id: int,
    action: str,
    changes: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            workspace_id=workspace_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=_serialize_changes(changes),
        )
    )


async def list_workspace_audit_logs(
    db: AsyncSession,
    workspace_id: int,
    skip: int,
    limit: int,
) -> tuple[list[AuditLog], int]:
    query = (
        select(AuditLog)
        .where(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(skip)
        .limit(limit)
    )
    count_query = select(func.count(AuditLog.id)).where(
        AuditLog.workspace_id == workspace_id
    )

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    return list(result.scalars().all()), int(count_result.scalar_one())
