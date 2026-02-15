from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
)
from app.security import get_current_user
from app.services import workspaces as workspace_service

router = APIRouter(tags=["Workspaces"])


@router.post(
    "/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await workspace_service.create_workspace(
        db,
        actor_user_id=current_user.id,
        data=data,
    )


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    return await workspace_service.list_workspaces(db, user_id=current_user.id)


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await workspace_service.get_workspace(
        db,
        workspace_id=workspace_id,
        user_id=current_user.id,
    )


@router.post(
    "/workspaces/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workspace_member(
    workspace_id: int,
    data: WorkspaceMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMemberResponse:
    return await workspace_service.add_workspace_member(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_user.id,
        data=data,
    )


@router.patch(
    "/workspaces/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
)
async def update_workspace_member(
    workspace_id: int,
    user_id: int,
    data: WorkspaceMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkspaceMemberResponse:
    return await workspace_service.update_workspace_member(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_user.id,
        target_user_id=user_id,
        data=data,
    )


@router.delete(
    "/workspaces/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_workspace_member(
    workspace_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await workspace_service.remove_workspace_member(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_user.id,
        target_user_id=user_id,
    )
