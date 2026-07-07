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
    active_provider = settings.ai_provider.strip().lower()
    if active_provider != "openai":
        record.provider = active_provider
        record.use_own_api_key = False
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
    active_provider = settings.ai_provider.strip().lower()
    record.provider = active_provider
    if active_provider != "openai":
        record.use_own_api_key = False

    if payload.useOwnApiKey is not None:
        if payload.useOwnApiKey and active_provider != "openai":
            raise HTTPException(status_code=400, detail="User-provided keys are only enabled for the OpenAI provider.")
        if payload.useOwnApiKey and not settings.allow_user_openai_keys:
            raise HTTPException(status_code=400, detail="User OpenAI API keys are disabled.")
        if payload.useOwnApiKey and not get_effective_plan_limits(current_user).can_use_own_api_key:
            raise HTTPException(status_code=403, detail="Current plan does not allow user OpenAI API keys.")
        record.use_own_api_key = payload.useOwnApiKey

    if payload.openaiApiKey:
        if active_provider != "openai":
            raise HTTPException(status_code=400, detail="User-provided keys are only enabled for the OpenAI provider.")
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
    record = get_or_create_user_ai_settings(db, current_user, settings)
    provider = settings.ai_provider.strip().lower()
    key = (payload.openaiApiKey or "").strip() if payload else ""
    if not key:
        if provider == "deepseek":
            if not settings.deepseek_api_key:
                raise HTTPException(status_code=400, detail="DeepSeek API key is missing.")
            key = settings.deepseek_api_key
        else:
            if not record.encrypted_openai_api_key:
                raise HTTPException(status_code=400, detail="OpenAI API key is missing.")
            try:
                key = decrypt_secret(record.encrypted_openai_api_key, settings)
            except RuntimeError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

    base_url = settings.deepseek_base_url.rstrip("/") if provider == "deepseek" else "https://api.openai.com/v1"
    provider_label = "DeepSeek" if provider == "deepseek" else "OpenAI"
    try:
        response = httpx.get(
            f"{base_url}/models",
            headers={"authorization": f"Bearer {key}"},
            timeout=10,
        )
    except httpx.RequestError:
        return OpenAiKeyTestResponse(ok=False, message=f"{provider_label} key test failed: network error.")

    if response.status_code == 200:
        return OpenAiKeyTestResponse(ok=True, message=f"{provider_label} key is valid.")
    return OpenAiKeyTestResponse(ok=False, message=f"{provider_label} key test failed with status {response.status_code}.")


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
    active_provider = settings.ai_provider.strip().lower()
    response_provider = active_provider if active_provider != "openai" else record.provider
    if record.provider == response_provider:
        default_model = record.default_model
        fallback_model = record.fallback_model
    elif response_provider == "deepseek":
        default_model = settings.deepseek_model
        fallback_model = settings.deepseek_fallback_model
    elif response_provider == "openai":
        default_model = settings.openai_model
        fallback_model = settings.openai_fallback_model
    else:
        default_model = record.default_model
        fallback_model = record.fallback_model
    return UserAiSettingsRead.model_validate(
        {
            "provider": response_provider,
            "use_own_api_key": record.use_own_api_key,
            "has_openai_api_key": bool(record.encrypted_openai_api_key),
            "masked_openai_api_key": masked_saved_openai_key(record, settings),
            "default_model": default_model,
            "fallback_model": fallback_model,
            "allow_user_openai_keys": settings.allow_user_openai_keys and response_provider == "openai",
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
    )
