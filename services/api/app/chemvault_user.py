from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.constants import SubscriptionStatus, UserPlan, UserRole
from app.models import Project, Subscription, User


@dataclass(frozen=True, slots=True)
class ChemVaultUserProfile:
    id: str
    email: str
    name: str | None
    role: str
    system_role: str
    status: str
    global_status: str
    raw: dict[str, Any]


def authenticate_chemvault_session(session_token: str, settings: Settings) -> ChemVaultUserProfile:
    profile = _fetch_user_profile(session_token, settings)
    if settings.chemvault_user_require_service_access:
        _assert_service_access(session_token, settings)
    return profile


def sync_chemvault_user(db: Session, profile: ChemVaultUserProfile, settings: Settings) -> User:
    email = profile.email.strip().lower()
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ChemVault user email is missing.")

    user = db.scalars(select(User).where(User.email == email)).first()
    if user is None:
        plan = _default_plan_for_profile(profile)
        user = User(
            email=email,
            name=profile.name,
            password_hash=None,
            role=_local_role_for_profile(profile),
            plan=plan,
            monthly_ai_file_limit=(
                1000000 if plan == UserPlan.ADMIN.value else settings.default_free_monthly_ai_file_limit
            ),
            monthly_ai_cost_limit_usd=(
                1000000.00 if plan == UserPlan.ADMIN.value else settings.default_free_monthly_ai_cost_limit_usd
            ),
        )
        db.add(user)
        db.flush()
        _ensure_default_resources(db, user, settings)
    else:
        user.name = profile.name or user.name
        user.role = _local_role_for_profile(profile)

    db.commit()
    db.refresh(user)
    return user


def _fetch_user_profile(session_token: str, settings: Settings) -> ChemVaultUserProfile:
    response = _get_user_center(
        "/api/auth/me",
        session_token=session_token,
        settings=settings,
    )
    if response.status_code == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ChemVault user session is invalid.")
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ChemVault user system could not validate the session.",
        )

    body = response.json()
    user = body.get("user") if isinstance(body, dict) else None
    if not isinstance(user, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ChemVault user system returned an invalid user response.",
        )

    if user.get("status") in {"disabled", "deleted"} or user.get("globalStatus") in {"disabled", "deleted"}:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ChemVault user account is not active.")

    return ChemVaultUserProfile(
        id=str(user.get("id") or ""),
        email=str(user.get("email") or ""),
        name=str(user.get("name")) if user.get("name") else None,
        role=str(user.get("role") or "free"),
        system_role=str(user.get("systemRole") or "user"),
        status=str(user.get("status") or "active"),
        global_status=str(user.get("globalStatus") or "active"),
        raw=user,
    )


def _assert_service_access(session_token: str, settings: Settings) -> None:
    response = _get_user_center(
        "/api/access/check",
        session_token=session_token,
        settings=settings,
        params={"service": settings.chemvault_user_service_key},
    )
    if response.status_code == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ChemVault user session is invalid.")
    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ChemVault user system could not check Extract access.",
        )
    body = response.json()
    if not isinstance(body, dict) or not body.get("allowed"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ChemVault Extract access is not enabled.")


def _get_user_center(
    path: str,
    *,
    session_token: str,
    settings: Settings,
    params: dict[str, str] | None = None,
) -> httpx.Response:
    base_url = settings.chemvault_user_base_url.rstrip("/")
    cookie_name = settings.chemvault_user_cookie_name
    try:
        return httpx.get(
            f"{base_url}{path}",
            params=params,
            headers={"cookie": f"{cookie_name}={session_token}"},
            timeout=settings.chemvault_user_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="ChemVault user system is unavailable.",
        ) from exc


def _local_role_for_profile(profile: ChemVaultUserProfile) -> str:
    if profile.role == "admin" or profile.system_role in {"admin", "super_admin", "owner"}:
        return UserRole.ADMIN.value
    return UserRole.USER.value


def _default_plan_for_profile(profile: ChemVaultUserProfile) -> str:
    if _local_role_for_profile(profile) == UserRole.ADMIN.value:
        return UserPlan.ADMIN.value
    return UserPlan.FREE.value


def _ensure_default_resources(db: Session, user: User, settings: Settings) -> None:
    from app.ai_settings import get_or_create_user_ai_settings

    has_project = db.scalars(select(Project.id).where(Project.user_id == user.id).limit(1)).first()
    if not has_project:
        db.add(Project(user_id=user.id, name=settings.default_project_name))

    has_subscription = db.scalars(select(Subscription.id).where(Subscription.user_id == user.id).limit(1)).first()
    if not has_subscription:
        db.add(
            Subscription(
                user_id=user.id,
                plan=user.plan or UserPlan.FREE.value,
                status=SubscriptionStatus.FREE.value,
                current_period_start=datetime.now(timezone.utc),
            )
        )

    get_or_create_user_ai_settings(db, user, settings)
