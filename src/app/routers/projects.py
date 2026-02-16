from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.security import get_current_user
from app.services import projects as project_service

router = APIRouter(tags=["Projects"])


@router.post(
    "/workspaces/{workspace_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    workspace_id: int,
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await project_service.create_project(
        db,
        workspace_id=workspace_id,
        actor_user_id=current_user.id,
        data=data,
    )
    return ProjectResponse.model_validate(project)


@router.get("/workspaces/{workspace_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    projects = await project_service.list_projects(
        db,
        workspace_id=workspace_id,
        user_id=current_user.id,
    )
    return [ProjectResponse.model_validate(project) for project in projects]


@router.get(
    "/workspaces/{workspace_id}/projects/{project_id}",
    response_model=ProjectResponse,
)
async def get_project(
    workspace_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await project_service.get_project(
        db,
        workspace_id=workspace_id,
        project_id=project_id,
        user_id=current_user.id,
    )
    return ProjectResponse.model_validate(project)


@router.patch(
    "/workspaces/{workspace_id}/projects/{project_id}",
    response_model=ProjectResponse,
)
async def update_project(
    workspace_id: int,
    project_id: int,
    data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await project_service.update_project(
        db,
        workspace_id=workspace_id,
        project_id=project_id,
        actor_user_id=current_user.id,
        data=data,
    )
    return ProjectResponse.model_validate(project)


@router.delete(
    "/workspaces/{workspace_id}/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    workspace_id: int,
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await project_service.delete_project(
        db,
        workspace_id=workspace_id,
        project_id=project_id,
        actor_user_id=current_user.id,
    )
