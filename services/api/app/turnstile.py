from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException, Request

from app.config import Settings

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile_response(token: str | None, settings: Settings, request: Request | None = None) -> None:
    secret = settings.turnstile_secret_key or settings.cloudflare_turnstile_secret_key
    if not secret and not settings.turnstile_required:
        return
    if not secret:
        raise HTTPException(status_code=500, detail="TURNSTILE_SECRET_KEY is missing.")
    if not token:
        raise HTTPException(status_code=400, detail="Cloudflare Turnstile verification is required.")

    payload = {"secret": secret, "response": token}
    remote_ip = _client_ip(request)
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        response = httpx.post(SITEVERIFY_URL, data=payload, timeout=settings.turnstile_timeout_seconds)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Cloudflare Turnstile verification could not be completed.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail="Cloudflare Turnstile verification returned an invalid response.",
        ) from exc

    if not result.get("success"):
        raise HTTPException(status_code=400, detail="Cloudflare Turnstile verification failed.")


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return None
