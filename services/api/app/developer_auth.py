from __future__ import annotations

import hmac
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api_keys import API_KEY_SCOPES, hash_api_key, is_api_key_active, key_prefix, validate_api_key_format
from app.auth.permissions import Permission, ProjectAccess, require_document_permission, require_project_permission
from app.database import get_db
from app.models import ApiKey, Document, Project, User
from app.rate_limit import enforce_rate_limit
from app.security import decode_access_token


@dataclass(slots=True)
class ApiActor:
    type: str
    user: User
    api_key: ApiKey | None = None
    user_id_value: str | None = None
    api_key_id_value: str | None = None
    workspace_id: str | None = None
    scopes: list[str] | None = None

    @property
    def user_id(self) -> str:
        return self.user_id_value or self.user.id

    @property
    def api_key_id(self) -> str | None:
        if self.api_key_id_value:
            return self.api_key_id_value
        return self.api_key.id if self.api_key else None

    def has_scope(self, scope: str) -> bool:
        if self.type == "user":
            return True
        return scope in set(self.scopes or [])


def get_current_actor(
    request: Request,
    db: Session = Depends(get_db),
) -> ApiActor:
    token = _extract_bearer_token(request) or request.headers.get("x-chemvault-api-key")
    if not token:
        raise _api_error(status.HTTP_401_UNAUTHORIZED, "unauthorized", "Authentication required.")

    if validate_api_key_format(token):
        actor = _actor_from_api_key(db, token)
    else:
        actor = _actor_from_jwt(db, token)

    request.state.actor = actor
    enforce_rate_limit(actor, db)
    return actor


def require_scope(scope: str):
    def dependency(actor: ApiActor = Depends(get_current_actor)) -> ApiActor:
        if not actor.has_scope(scope):
            raise _api_error(
                status.HTTP_403_FORBIDDEN,
                "insufficient_scope",
                f"API key requires scope: {scope}.",
                {"required_scope": scope},
            )
        return actor

    return dependency


def require_project_scope_and_permission(
    db: Session,
    actor: ApiActor,
    project_id: str,
    *,
    scope: str,
    permission: Permission,
) -> ProjectAccess:
    if not actor.has_scope(scope):
        raise _api_error(
            status.HTTP_403_FORBIDDEN,
            "insufficient_scope",
            f"API key requires scope: {scope}.",
            {"required_scope": scope},
        )
    access = require_project_permission(db, project_id, actor.user, permission)
    if actor.workspace_id and access.workspace_id != actor.workspace_id:
        raise _api_error(status.HTTP_403_FORBIDDEN, "forbidden", "API key cannot access this workspace.")
    return access


def require_document_scope_and_permission(
    db: Session,
    actor: ApiActor,
    document_id: str,
    *,
    scope: str,
    permission: Permission,
) -> tuple[Document, ProjectAccess]:
    if not actor.has_scope(scope):
        raise _api_error(
            status.HTTP_403_FORBIDDEN,
            "insufficient_scope",
            f"API key requires scope: {scope}.",
            {"required_scope": scope},
        )
    document, access = require_document_permission(db, document_id, actor.user, permission)
    if actor.workspace_id and access.workspace_id != actor.workspace_id:
        raise _api_error(status.HTTP_403_FORBIDDEN, "forbidden", "API key cannot access this workspace.")
    return document, access


def _actor_from_api_key(db: Session, token: str) -> ApiActor:
    hashed = hash_api_key(token)
    prefix = key_prefix(token)
    candidates = db.scalars(select(ApiKey).where(ApiKey.key_prefix == prefix)).all()
    api_key = next((candidate for candidate in candidates if hmac.compare_digest(candidate.key_hash, hashed)), None)
    if api_key is None:
        raise _api_error(status.HTTP_401_UNAUTHORIZED, "unauthorized", "Invalid API key.")

    active, code = is_api_key_active(api_key)
    if not active:
        message = "API key has been revoked." if code == "api_key_revoked" else "API key has expired."
        raise _api_error(status.HTTP_401_UNAUTHORIZED, code or "unauthorized", message)

    user = db.get(User, api_key.user_id)
    if user is None:
        raise _api_error(status.HTTP_401_UNAUTHORIZED, "unauthorized", "API key owner was not found.")

    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(api_key)
    return ApiActor(
        type="api_key",
        user=user,
        api_key=api_key,
        user_id_value=user.id,
        api_key_id_value=api_key.id,
        workspace_id=api_key.workspace_id,
        scopes=list(api_key.scopes or []),
    )


def _actor_from_jwt(db: Session, token: str) -> ApiActor:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise _api_error(status.HTTP_401_UNAUTHORIZED, "unauthorized", str(exc)) from exc
    user = db.get(User, payload["sub"])
    if user is None:
        raise _api_error(status.HTTP_401_UNAUTHORIZED, "unauthorized", "User not found.")
    return ApiActor(type="user", user=user, user_id_value=user.id, scopes=sorted(API_KEY_SCOPES))


def _extract_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization")
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()


def _api_error(status_code: int, code: str, message: str, details: dict | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details or {}},
    )
