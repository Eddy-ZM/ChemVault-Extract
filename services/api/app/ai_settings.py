from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.config.ai import AISettings, get_ai_settings
from app.models import ExtractionJob, User, UserAiSettings
from app.security import decrypt_secret, mask_secret


def get_or_create_user_ai_settings(db: Session, user: User, settings: Settings | None = None) -> UserAiSettings:
    resolved = settings or get_settings()
    record = db.scalars(select(UserAiSettings).where(UserAiSettings.user_id == user.id)).first()
    if record is not None:
        return record
    record = UserAiSettings(
        user_id=user.id,
        provider=resolved.ai_provider,
        use_own_api_key=False,
        default_model=resolved.openai_model,
        fallback_model=resolved.openai_fallback_model,
    )
    db.add(record)
    db.flush()
    return record


def build_ai_settings_for_user(
    db: Session,
    user: User,
    settings: Settings | None = None,
    *,
    include_api_key: bool = False,
) -> AISettings:
    resolved = settings or get_settings()
    ai_settings = get_ai_settings(resolved)
    record = get_or_create_user_ai_settings(db, user, resolved)
    ai_settings.provider = resolved.ai_provider if resolved.ai_provider != "openai" else (record.provider or ai_settings.provider)
    ai_settings.default_model = record.default_model or ai_settings.default_model
    ai_settings.fallback_model = record.fallback_model or ai_settings.fallback_model

    if not include_api_key or ai_settings.provider != "openai":
        ai_settings.openai_api_key = None
        return ai_settings

    if record.use_own_api_key:
        if not record.encrypted_openai_api_key:
            raise RuntimeError("User OpenAI API key is missing.")
        ai_settings.openai_api_key = decrypt_secret(record.encrypted_openai_api_key, resolved)
    else:
        if not resolved.openai_api_key:
            raise RuntimeError("Platform OpenAI API key is missing.")
        ai_settings.openai_api_key = resolved.openai_api_key
    return ai_settings


def build_ai_settings_for_job(
    db: Session,
    job: ExtractionJob,
    settings: Settings | None = None,
    *,
    include_api_key: bool = False,
) -> AISettings:
    user = job.document.project.user
    return build_ai_settings_for_user(db, user, settings, include_api_key=include_api_key)


def user_uses_own_openai_key(db: Session, user: User, settings: Settings | None = None) -> bool:
    record = get_or_create_user_ai_settings(db, user, settings or get_settings())
    return bool(record.use_own_api_key)


def masked_saved_openai_key(record: UserAiSettings | None, settings: Settings | None = None) -> str | None:
    if record is None or not record.encrypted_openai_api_key:
        return None
    try:
        return mask_secret(decrypt_secret(record.encrypted_openai_api_key, settings or get_settings()))
    except RuntimeError:
        return "sk-****"
