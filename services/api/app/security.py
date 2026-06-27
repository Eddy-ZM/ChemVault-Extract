from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.chemvault_user import authenticate_chemvault_session, sync_chemvault_user
from app.database import get_db
from app.models import User

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return password_context.verify(password, password_hash)


def create_access_token(user: User, settings: Settings | None = None) -> str:
    resolved = settings or get_settings()
    if not resolved.jwt_secret:
        raise RuntimeError("JWT_SECRET is missing.")
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=resolved.jwt_expires_in_minutes)).timestamp()),
    }
    return _encode_jwt(payload, resolved.jwt_secret)


def decode_access_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    resolved = settings or get_settings()
    if not resolved.jwt_secret:
        raise ValueError("JWT_SECRET is missing.")
    payload = _decode_jwt(token, resolved.jwt_secret)
    expires_at = payload.get("exp")
    if not isinstance(expires_at, int) or expires_at < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Token has expired.")
    if not payload.get("sub"):
        raise ValueError("Token subject is missing.")
    return payload


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is not None and credentials.scheme.lower() == "bearer":
        try:
            payload = decode_access_token(credentials.credentials)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

        user = db.get(User, payload["sub"])
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
        return user

    settings = get_settings()
    session_token = request.cookies.get(settings.chemvault_user_cookie_name)
    if session_token:
        profile = authenticate_chemvault_session(session_token, settings)
        return sync_chemvault_user(db, profile, settings)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    return current_user


def encrypt_secret(value: str, settings: Settings | None = None) -> str:
    resolved = settings or get_settings()
    if not resolved.app_encryption_key:
        raise RuntimeError("APP_ENCRYPTION_KEY is missing. User OpenAI API keys cannot be saved.")
    return _fernet(resolved.app_encryption_key).encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str, settings: Settings | None = None) -> str:
    resolved = settings or get_settings()
    if not resolved.app_encryption_key:
        raise RuntimeError("APP_ENCRYPTION_KEY is missing. User OpenAI API keys cannot be read.")
    try:
        return _fernet(resolved.app_encryption_key).decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Stored OpenAI API key could not be decrypted.") from exc


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "****"
    prefix = value[:3] if value.startswith("sk-") else value[:2]
    return f"{prefix}****{value[-4:]}"


def _encode_jwt(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = ".".join(
        [
            _base64url(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")),
            _base64url(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")),
        ]
    )
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest()
    return f"{signing_input}.{_base64url(signature)}"


def _decode_jwt(token: str, secret: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token.")
    signing_input = ".".join(parts[:2])
    expected = _base64url(hmac.new(secret.encode("utf-8"), signing_input.encode("utf-8"), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, parts[2]):
        raise ValueError("Invalid token signature.")
    try:
        return json.loads(_base64url_decode(parts[1]).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid token payload.") from exc


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _fernet(secret: str) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode("utf-8")).digest())
    return Fernet(key)
