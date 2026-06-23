from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants import WorkspaceMemberStatus, WorkspaceRole
from app.models import Document, Project, User, Workspace, WorkspaceMember


class Permission(StrEnum):
    VIEW = "view"
    MANAGE_WORKSPACE = "manage_workspace"
    INVITE_MEMBER = "invite_member"
    REMOVE_MEMBER = "remove_member"
    CREATE_PROJECT = "create_project"
    UPLOAD = "upload"
    RUN_AI = "run_ai"
    BATCH_EXTRACT = "batch_extract"
    REVIEW = "review"
    EXPORT = "export"
    MANAGE_BILLING = "manage_billing"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    WorkspaceRole.OWNER.value: {
        Permission.VIEW,
        Permission.MANAGE_WORKSPACE,
        Permission.INVITE_MEMBER,
        Permission.REMOVE_MEMBER,
        Permission.CREATE_PROJECT,
        Permission.UPLOAD,
        Permission.RUN_AI,
        Permission.BATCH_EXTRACT,
        Permission.REVIEW,
        Permission.EXPORT,
        Permission.MANAGE_BILLING,
    },
    WorkspaceRole.ADMIN.value: {
        Permission.VIEW,
        Permission.MANAGE_WORKSPACE,
        Permission.INVITE_MEMBER,
        Permission.REMOVE_MEMBER,
        Permission.CREATE_PROJECT,
        Permission.UPLOAD,
        Permission.RUN_AI,
        Permission.BATCH_EXTRACT,
        Permission.REVIEW,
        Permission.EXPORT,
    },
    WorkspaceRole.MEMBER.value: {
        Permission.VIEW,
        Permission.UPLOAD,
        Permission.RUN_AI,
        Permission.REVIEW,
        Permission.EXPORT,
    },
    WorkspaceRole.VIEWER.value: {
        Permission.VIEW,
    },
}


@dataclass(slots=True)
class WorkspaceAccess:
    workspace: Workspace
    member: WorkspaceMember
    role: str

    def can(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())


@dataclass(slots=True)
class ProjectAccess:
    project: Project
    role: str
    workspace: Workspace | None
    billing_user: User

    def can(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, set())

    @property
    def workspace_id(self) -> str | None:
        return self.workspace.id if self.workspace else None


def active_workspace_member(db: Session, workspace_id: str, user: User) -> WorkspaceMember | None:
    return db.scalars(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.status == WorkspaceMemberStatus.ACTIVE.value,
        )
    ).first()


def workspace_access(db: Session, workspace_id: str, user: User) -> WorkspaceAccess:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or workspace.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    member = active_workspace_member(db, workspace_id, user)
    if member is None:
        raise HTTPException(status_code=403, detail="You do not have access to this workspace.")
    return WorkspaceAccess(workspace=workspace, member=member, role=member.role)


def require_workspace_permission(
    db: Session,
    workspace_id: str,
    user: User,
    permission: Permission,
) -> WorkspaceAccess:
    access = workspace_access(db, workspace_id, user)
    if not access.can(permission):
        raise HTTPException(status_code=403, detail=f"Workspace role cannot {permission.value}.")
    return access


def project_access(db: Session, project_id: str, user: User) -> ProjectAccess:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")

    if project.workspace_id:
        workspace = project.workspace or db.get(Workspace, project.workspace_id)
        if workspace is None or workspace.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Workspace not found.")
        member = active_workspace_member(db, workspace.id, user)
        if member is None:
            raise HTTPException(status_code=403, detail="You do not have access to this project.")
        return ProjectAccess(project=project, role=member.role, workspace=workspace, billing_user=workspace.owner)

    if project.user_id == user.id:
        return ProjectAccess(project=project, role=WorkspaceRole.OWNER.value, workspace=None, billing_user=user)

    raise HTTPException(status_code=403, detail="You do not have access to this project.")


def require_project_permission(
    db: Session,
    project_id: str,
    user: User,
    permission: Permission,
) -> ProjectAccess:
    access = project_access(db, project_id, user)
    if not access.can(permission):
        raise HTTPException(status_code=403, detail=f"Project role cannot {permission.value}.")
    return access


def document_project_access(db: Session, document_id: str, user: User) -> tuple[Document, ProjectAccess]:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    access = project_access(db, document.project_id, user)
    return document, access


def require_document_permission(
    db: Session,
    document_id: str,
    user: User,
    permission: Permission,
) -> tuple[Document, ProjectAccess]:
    document, access = document_project_access(db, document_id, user)
    if not access.can(permission):
        raise HTTPException(status_code=403, detail=f"Project role cannot {permission.value}.")
    return document, access


def accessible_workspace_ids(db: Session, user: User) -> list[str]:
    return db.scalars(
        select(WorkspaceMember.workspace_id).where(
            WorkspaceMember.user_id == user.id,
            WorkspaceMember.status == WorkspaceMemberStatus.ACTIVE.value,
        )
    ).all()


def can_role(permission: Permission, role: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
