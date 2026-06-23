from __future__ import annotations

from typing import Any

import httpx
from fastapi import HTTPException

from app.config import Settings, get_settings

STRIPE_API_BASE_URL = "https://api.stripe.com/v1"
STRIPE_API_VERSION = "2026-02-25.clover"


class StripeClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.stripe_secret_key:
            raise HTTPException(status_code=500, detail="STRIPE_SECRET_KEY is missing.")

    def create_customer(self, *, email: str, name: str | None, user_id: str) -> dict[str, Any]:
        return self._post(
            "/customers",
            {
                "email": email,
                "metadata[userId]": user_id,
                **({"name": name} if name else {}),
            },
        )

    def create_checkout_session(
        self,
        *,
        customer_id: str,
        price_id: str,
        user_id: str,
        plan: str,
        success_url: str,
        cancel_url: str,
    ) -> dict[str, Any]:
        return self._post(
            "/checkout/sessions",
            {
                "mode": "subscription",
                "customer": customer_id,
                "success_url": success_url,
                "cancel_url": cancel_url,
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": "1",
                "metadata[userId]": user_id,
                "metadata[plan]": plan,
                "subscription_data[metadata][userId]": user_id,
                "subscription_data[metadata][plan]": plan,
            },
        )

    def create_customer_portal_session(self, *, customer_id: str, return_url: str) -> dict[str, Any]:
        return self._post(
            "/billing_portal/sessions",
            {
                "customer": customer_id,
                "return_url": return_url,
            },
        )

    def retrieve_subscription(self, subscription_id: str) -> dict[str, Any]:
        return self._get(f"/subscriptions/{subscription_id}")

    def _headers(self) -> dict[str, str]:
        return {
            "authorization": f"Bearer {self.settings.stripe_secret_key}",
            "stripe-version": STRIPE_API_VERSION,
        }

    def _post(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        try:
            response = httpx.post(
                f"{STRIPE_API_BASE_URL}{path}",
                data=data,
                headers=self._headers(),
                timeout=20,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail="Stripe request failed.") from exc
        return self._json_or_raise(response)

    def _get(self, path: str) -> dict[str, Any]:
        try:
            response = httpx.get(
                f"{STRIPE_API_BASE_URL}{path}",
                headers=self._headers(),
                timeout=20,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail="Stripe request failed.") from exc
        return self._json_or_raise(response)

    def _json_or_raise(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code < 400:
            return response.json()
        try:
            payload = response.json()
            message = payload.get("error", {}).get("message") or response.text
        except ValueError:
            message = response.text
        raise HTTPException(status_code=502, detail=f"Stripe error: {message}")
