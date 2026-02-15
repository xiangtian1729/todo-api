import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError
from app.models.idempotency_key import IdempotencyKey

IDEMPOTENCY_TTL = timedelta(hours=24)


def build_request_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _naive_utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _comparison_now(expires_at: datetime) -> datetime:
    if expires_at.tzinfo is not None:
        return datetime.now(expires_at.tzinfo)
    return _naive_utc_now()


async def get_replay_response(
    db: AsyncSession,
    *,
    user_id: int,
    route: str,
    key: str,
    request_hash: str,
) -> tuple[dict[str, Any] | None, IdempotencyKey | None]:
    result = await db.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.user_id == user_id,
            IdempotencyKey.route == route,
            IdempotencyKey.key == key,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None, None

    now = _comparison_now(record.expires_at)
    if record.expires_at <= now:
        return None, record

    if record.request_hash != request_hash:
        raise ConflictError("Idempotency key payload conflict")

    return json.loads(record.response_body), record


async def save_response(
    db: AsyncSession,
    *,
    existing_record: IdempotencyKey | None,
    user_id: int,
    route: str,
    key: str,
    request_hash: str,
    response_status: int,
    response_body: dict[str, Any],
    resource_type: str,
    resource_id: int,
) -> None:
    now = _naive_utc_now()
    expires_at = now + IDEMPOTENCY_TTL

    if existing_record is None:
        db.add(
            IdempotencyKey(
                user_id=user_id,
                route=route,
                key=key,
                request_hash=request_hash,
                response_status=response_status,
                response_body=json.dumps(response_body, default=str),
                resource_type=resource_type,
                resource_id=resource_id,
                expires_at=expires_at,
            )
        )
        return

    existing_record.request_hash = request_hash
    existing_record.response_status = response_status
    existing_record.response_body = json.dumps(response_body, default=str)
    existing_record.resource_type = resource_type
    existing_record.resource_id = resource_id
    existing_record.expires_at = expires_at
