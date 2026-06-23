from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api_keys import API_KEY_SCOPES, generate_api_key, hash_api_key, key_prefix, mask_api_key
from app.auth.permissions import Permission, require_workspace_permission
from app.database import get_db
from app.models import ApiKey, User
from app.schemas import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyRead, ApiKeyRevokeResponse
from app.security import get_current_user

router = APIRouter(prefix="/settings/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyRead])
def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ApiKeyRead]:
    records = db.scalars(
        select(ApiKey)
        .where(ApiKey.user_id == current_user.id)
        .order_by(ApiKey.created_at.desc(), ApiKey.id.desc())
    ).all()
    return [ApiKeyRead.model_validate(record) for record in records]


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: ApiKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiKeyCreateResponse:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="API key name is required.")
    scopes = sorted(set(payload.scopes))
    invalid_scopes = [scope for scope in scopes if scope not in API_KEY_SCOPES]
    if invalid_scopes:
        raise HTTPException(status_code=400, detail=f"Invalid scopes: {', '.join(invalid_scopes)}")
    if not scopes:
        raise HTTPException(status_code=400, detail="At least one API scope is required.")

    workspace_id = payload.resolved_workspace_id
    if workspace_id:
        require_workspace_permission(db, workspace_id, current_user, Permission.VIEW)

    expires_at = None
    if payload.expiresInDays is not None:
        if payload.expiresInDays <= 0 or payload.expiresInDays > 3650:
            raise HTTPException(status_code=400, detail="expiresInDays must be between 1 and 3650.")
        expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expiresInDays)

    plain_key = generate_api_key(test_mode=False)
    record = ApiKey(
        user_id=current_user.id,
        workspace_id=workspace_id,
        name=name,
        key_hash=hash_api_key(plain_key),
        key_prefix=key_prefix(plain_key),
        masked_key=mask_api_key(plain_key),
        scopes=scopes,
        expires_at=expires_at,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return ApiKeyCreateResponse.model_validate(
        {
            "id": record.id,
            "workspace_id": record.workspace_id,
            "name": record.name,
            "key_prefix": record.key_prefix,
            "masked_key": record.masked_key,
            "scopes": record.scopes or [],
            "last_used_at": record.last_used_at,
            "expires_at": record.expires_at,
            "revoked_at": record.revoked_at,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "plain_key": plain_key,
        }
    )


@router.post("/{api_key_id}/revoke", response_model=ApiKeyRevokeResponse)
def revoke_api_key(
    api_key_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiKeyRevokeResponse:
    record = db.get(ApiKey, api_key_id)
    if record is None or record.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="API key not found.")
    if record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(record)
    return ApiKeyRevokeResponse.model_validate({"id": record.id, "revoked_at": record.revoked_at})
