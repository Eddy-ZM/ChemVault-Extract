from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.billing.enforcement import assert_can_create_project
from app.auth.permissions import Permission, accessible_workspace_ids, require_workspace_permission
from app.database import get_db
from app.models import Project, User
from app.schemas import ProjectCreateRequest, ProjectRead
from app.security import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ProjectRead]:
    workspace_ids = accessible_workspace_ids(db, current_user)
    filters = [and_(Project.user_id == current_user.id, Project.workspace_id.is_(None))]
    if workspace_ids:
        filters.append(Project.workspace_id.in_(workspace_ids))
    projects = db.scalars(
        select(Project).where(or_(*filters)).order_by(Project.created_at.desc(), Project.id.desc())
    ).all()
    return [ProjectRead.model_validate(project) for project in projects]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectRead:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Project name is required.")
    workspace_id = payload.resolved_workspace_id
    if workspace_id:
        access = require_workspace_permission(db, workspace_id, current_user, Permission.CREATE_PROJECT)
        assert_can_create_project(db, access.workspace.owner, access.workspace)
        project = Project(user_id=current_user.id, workspace_id=workspace_id, name=name)
    else:
        assert_can_create_project(db, current_user)
        project = Project(user_id=current_user.id, name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectRead.model_validate(project)
