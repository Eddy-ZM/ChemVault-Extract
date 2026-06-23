from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_settings import get_or_create_user_ai_settings
from app.config import get_settings
from app.constants import SubscriptionStatus, UserPlan, UserRole
from app.database import get_db
from app.models import Project, Subscription, User
from app.schemas import AuthLoginRequest, AuthRegisterRequest, AuthTokenResponse, UserRead
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    settings = get_settings()
    _assert_jwt_configured(settings)
    email = payload.email.strip().lower()
    if db.scalars(select(User).where(User.email == email)).first() is not None:
        raise HTTPException(status_code=409, detail="Email is already registered.")

    user = User(
        email=email,
        name=(payload.name or "").strip() or None,
        password_hash=hash_password(payload.password),
        role=UserRole.USER.value,
        plan=UserPlan.FREE.value,
        monthly_ai_file_limit=settings.default_free_monthly_ai_file_limit,
        monthly_ai_cost_limit_usd=settings.default_free_monthly_ai_cost_limit_usd,
    )
    db.add(user)
    db.flush()
    db.add(Project(user_id=user.id, name=settings.default_project_name))
    db.add(
        Subscription(
            user_id=user.id,
            plan=UserPlan.FREE.value,
            status=SubscriptionStatus.FREE.value,
            current_period_start=datetime.now(timezone.utc),
        )
    )
    get_or_create_user_ai_settings(db, user, settings)
    db.commit()
    db.refresh(user)
    return _auth_response(user)


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    _assert_jwt_configured(get_settings())
    user = db.scalars(select(User).where(User.email == payload.email.strip().lower())).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return _auth_response(user)


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


def _auth_response(user: User) -> AuthTokenResponse:
    try:
        token = create_access_token(user)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return AuthTokenResponse.model_validate(
        {
            "access_token": token,
            "token_type": "bearer",
            "user": UserRead.model_validate(user),
        }
    )


def _assert_jwt_configured(settings) -> None:
    if not settings.jwt_secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET is missing.")
