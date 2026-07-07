from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.permissions import Permission, require_workspace_permission, workspace_access
from app.billing.enforcement import assert_can_create_workspace, assert_can_invite_member
from app.constants import UserPlan, WorkspaceMemberStatus, WorkspaceRole
from app.database import get_db
from app.models import Project, User, Workspace, WorkspaceMember
from app.notifications import send_workspace_invite_notification
from app.schemas import (
    ProjectRead,
    WorkspaceCreateRequest,
    WorkspaceDetailRead,
    WorkspaceInviteAcceptResponse,
    WorkspaceInviteRequest,
    WorkspaceMemberRead,
    WorkspaceMemberUpdateRequest,
    WorkspaceRead,
    WorkspaceUpdateRequest,
)
from app.security import get_current_user

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceDetailRead, status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceDetailRead:
    assert_can_create_workspace(current_user)
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Workspace name is required.")
    workspace = Workspace(name=name, owner_user_id=current_user.id, plan=UserPlan.LAB.value)
    db.add(workspace)
    db.flush()
    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role=WorkspaceRole.OWNER.value,
        status=WorkspaceMemberStatus.ACTIVE.value,
        invited_email=current_user.email,
        invited_by_user_id=current_user.id,
        joined_at=datetime.now(timezone.utc),
    )
    db.add(member)
    db.commit()
    db.refresh(workspace)
    return _workspace_detail(db, workspace)


@router.get("", response_model=list[WorkspaceRead])
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WorkspaceRead]:
    workspaces = db.scalars(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.status == WorkspaceMemberStatus.ACTIVE.value,
            Workspace.deleted_at.is_(None),
        )
        .order_by(Workspace.created_at.desc(), Workspace.id.desc())
    ).all()
    return [WorkspaceRead.model_validate(workspace) for workspace in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceDetailRead)
def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceDetailRead:
    access = workspace_access(db, workspace_id, current_user)
    return _workspace_detail(db, access.workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceDetailRead)
def update_workspace(
    workspace_id: str,
    payload: WorkspaceUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceDetailRead:
    access = require_workspace_permission(db, workspace_id, current_user, Permission.MANAGE_WORKSPACE)
    if access.role not in {WorkspaceRole.OWNER.value, WorkspaceRole.ADMIN.value}:
        raise HTTPException(status_code=403, detail="Workspace role cannot update workspace.")
    if payload.name is not None:
        name = payload.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Workspace name is required.")
        access.workspace.name = name
    db.commit()
    db.refresh(access.workspace)
    return _workspace_detail(db, access.workspace)


@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    access = require_workspace_permission(db, workspace_id, current_user, Permission.MANAGE_WORKSPACE)
    if access.role != WorkspaceRole.OWNER.value:
        raise HTTPException(status_code=403, detail="Only workspace owner can delete workspace.")
    access.workspace.deleted_at = datetime.now(timezone.utc)
    for member in access.workspace.members:
        if member.role != WorkspaceRole.OWNER.value:
            member.status = WorkspaceMemberStatus.REMOVED.value
    db.commit()
    return {"status": "ok"}


@router.post("/{workspace_id}/invites", response_model=WorkspaceMemberRead, status_code=status.HTTP_201_CREATED)
def invite_workspace_member(
    workspace_id: str,
    payload: WorkspaceInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceMemberRead:
    access = require_workspace_permission(db, workspace_id, current_user, Permission.INVITE_MEMBER)
    role = payload.role.strip().lower()
    if role == WorkspaceRole.OWNER.value:
        raise HTTPException(status_code=400, detail="Cannot invite a member as owner.")
    if role not in {WorkspaceRole.ADMIN.value, WorkspaceRole.MEMBER.value, WorkspaceRole.VIEWER.value}:
        raise HTTPException(status_code=400, detail="Unsupported workspace role.")
    email = payload.email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Invite email is required.")
    assert_can_invite_member(db, current_user, access.workspace)

    existing = db.scalars(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.invited_email == email,
            WorkspaceMember.status != WorkspaceMemberStatus.REMOVED.value,
        )
    ).first()
    if existing is not None:
        existing.role = role
        existing.status = WorkspaceMemberStatus.INVITED.value if existing.user_id is None else existing.status
        existing.invited_by_user_id = current_user.id
        db.commit()
        db.refresh(existing)
        send_workspace_invite_notification(workspace=access.workspace, member=existing)
        return WorkspaceMemberRead.model_validate(existing)

    user = db.scalars(select(User).where(User.email == email)).first()
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=None,
        role=role,
        status=WorkspaceMemberStatus.INVITED.value,
        invited_email=email,
        invited_by_user_id=current_user.id,
    )
    if user is not None:
        member.user_id = user.id
    db.add(member)
    db.commit()
    db.refresh(member)
    send_workspace_invite_notification(workspace=access.workspace, member=member)
    return WorkspaceMemberRead.model_validate(member)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberRead])
def list_workspace_members(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[WorkspaceMemberRead]:
    workspace_access(db, workspace_id, current_user)
    members = db.scalars(
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.status != WorkspaceMemberStatus.REMOVED.value)
        .order_by(WorkspaceMember.created_at, WorkspaceMember.id)
    ).all()
    return [WorkspaceMemberRead.model_validate(member) for member in members]


@router.patch("/{workspace_id}/members/{member_id}", response_model=WorkspaceMemberRead)
def update_workspace_member(
    workspace_id: str,
    member_id: str,
    payload: WorkspaceMemberUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceMemberRead:
    access = require_workspace_permission(db, workspace_id, current_user, Permission.INVITE_MEMBER)
    member = _member_or_404(db, workspace_id, member_id)
    if member.role == WorkspaceRole.OWNER.value:
        raise HTTPException(status_code=400, detail="Cannot change workspace owner role.")
    role = payload.role.strip().lower()
    if role == WorkspaceRole.OWNER.value:
        raise HTTPException(status_code=400, detail="Cannot promote a member to owner.")
    if role not in {WorkspaceRole.ADMIN.value, WorkspaceRole.MEMBER.value, WorkspaceRole.VIEWER.value}:
        raise HTTPException(status_code=400, detail="Unsupported workspace role.")
    member.role = role
    db.commit()
    db.refresh(member)
    return WorkspaceMemberRead.model_validate(member)


@router.delete("/{workspace_id}/members/{member_id}")
def remove_workspace_member(
    workspace_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    require_workspace_permission(db, workspace_id, current_user, Permission.REMOVE_MEMBER)
    member = _member_or_404(db, workspace_id, member_id)
    if member.role == WorkspaceRole.OWNER.value:
        raise HTTPException(status_code=400, detail="Cannot remove workspace owner.")
    member.status = WorkspaceMemberStatus.REMOVED.value
    db.commit()
    return {"status": "ok"}


@router.post("/invites/{invite_id}/accept", response_model=WorkspaceInviteAcceptResponse)
def accept_workspace_invite(
    invite_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceInviteAcceptResponse:
    member = db.scalars(
        select(WorkspaceMember).where(
            (WorkspaceMember.id == invite_id) | (WorkspaceMember.invite_token == invite_id),
            WorkspaceMember.status == WorkspaceMemberStatus.INVITED.value,
        )
    ).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Invite not found.")
    if member.invited_email and member.invited_email.lower() != current_user.email.lower():
        raise HTTPException(status_code=403, detail="Invite email does not match current user.")
    member.user_id = current_user.id
    member.status = WorkspaceMemberStatus.ACTIVE.value
    member.joined_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(member)
    return WorkspaceInviteAcceptResponse.model_validate(
        {"workspace": WorkspaceRead.model_validate(member.workspace), "member": WorkspaceMemberRead.model_validate(member)}
    )


def _workspace_detail(db: Session, workspace: Workspace) -> WorkspaceDetailRead:
    members = db.scalars(
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace.id, WorkspaceMember.status != WorkspaceMemberStatus.REMOVED.value)
        .order_by(WorkspaceMember.created_at, WorkspaceMember.id)
    ).all()
    projects = db.scalars(
        select(Project).where(Project.workspace_id == workspace.id).order_by(Project.created_at.desc(), Project.id.desc())
    ).all()
    return WorkspaceDetailRead.model_validate(
        {
            **WorkspaceRead.model_validate(workspace).model_dump(),
            "members": [WorkspaceMemberRead.model_validate(member) for member in members],
            "projects": [ProjectRead.model_validate(project) for project in projects],
        }
    )


def _member_or_404(db: Session, workspace_id: str, member_id: str) -> WorkspaceMember:
    member = db.scalars(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.id == member_id)
    ).first()
    if member is None:
        raise HTTPException(status_code=404, detail="Workspace member not found.")
    return member
