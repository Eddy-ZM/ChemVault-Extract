from __future__ import annotations

import httpx
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai_settings import get_or_create_user_ai_settings, masked_saved_openai_key
from app.billing.plans import get_effective_plan_limits
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import OpenAiKeyTestRequest, OpenAiKeyTestResponse, UserAiSettingsRead, UserAiSettingsUpdate
from app.security import decrypt_secret, encrypt_secret, get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/ai", response_model=UserAiSettingsRead)
def get_ai_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserAiSettingsRead:
    settings = get_settings()
    record = get_or_create_user_ai_settings(db, current_user, settings)
    db.commit()
    db.refresh(record)
    return _settings_response(record)


@router.post("/ai", response_model=UserAiSettingsRead)
def update_ai_settings(
    payload: UserAiSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserAiSettingsRead:
    settings = get_settings()
    record = get_or_create_user_ai_settings(db, current_user, settings)

    if payload.useOwnApiKey is not None:
        if payload.useOwnApiKey and not settings.allow_user_openai_keys:
            raise HTTPException(status_code=400, detail="User OpenAI API keys are disabled.")
        if payload.useOwnApiKey and not get_effective_plan_limits(current_user).can_use_own_api_key:
            raise HTTPException(status_code=403, detail="Current plan does not allow user OpenAI API keys.")
        record.use_own_api_key = payload.useOwnApiKey

    if payload.openaiApiKey:
        if not settings.allow_user_openai_keys:
            raise HTTPException(status_code=400, detail="User OpenAI API keys are disabled.")
        if not get_effective_plan_limits(current_user).can_use_own_api_key:
            raise HTTPException(status_code=403, detail="Current plan does not allow user OpenAI API keys.")
        try:
            record.encrypted_openai_api_key = encrypt_secret(payload.openaiApiKey.strip(), settings)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        record.use_own_api_key = True

    if payload.defaultModel:
        record.default_model = payload.defaultModel.strip()
    if payload.fallbackModel:
        record.fallback_model = payload.fallbackModel.strip()

    db.commit()
    db.refresh(record)
    return _settings_response(record)


@router.post("/ai/test-openai-key", response_model=OpenAiKeyTestResponse)
def test_openai_key(
    payload: OpenAiKeyTestRequest | None = Body(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OpenAiKeyTestResponse:
    settings = get_settings()
    key = (payload.openaiApiKey or "").strip() if payload else ""
    if not key:
        record = get_or_create_user_ai_settings(db, current_user, settings)
        if not record.encrypted_openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is missing.")
        try:
            key = decrypt_secret(record.encrypted_openai_api_key, settings)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        response = httpx.get(
            "https://api.openai.com/v1/models",
            headers={"authorization": f"Bearer {key}"},
            timeout=10,
        )
    except httpx.RequestError:
        return OpenAiKeyTestResponse(ok=False, message="OpenAI key test failed: network error.")

    if response.status_code == 200:
        return OpenAiKeyTestResponse(ok=True, message="OpenAI key is valid.")
    return OpenAiKeyTestResponse(ok=False, message=f"OpenAI key test failed with status {response.status_code}.")


@router.delete("/ai/openai-key", response_model=UserAiSettingsRead)
def delete_openai_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserAiSettingsRead:
    record = get_or_create_user_ai_settings(db, current_user, get_settings())
    record.encrypted_openai_api_key = None
    record.use_own_api_key = False
    db.commit()
    db.refresh(record)
    return _settings_response(record)


def _settings_response(record) -> UserAiSettingsRead:
    settings = get_settings()
    return UserAiSettingsRead.model_validate(
        {
            "provider": record.provider,
            "use_own_api_key": record.use_own_api_key,
            "has_openai_api_key": bool(record.encrypted_openai_api_key),
            "masked_openai_api_key": masked_saved_openai_key(record, settings),
            "default_model": record.default_model,
            "fallback_model": record.fallback_model,
            "allow_user_openai_keys": settings.allow_user_openai_keys,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
    )
