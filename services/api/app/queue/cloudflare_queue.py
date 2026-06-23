from __future__ import annotations

import httpx

from app.config import Settings


class CloudflareQueue:
    """Cloudflare Queue publisher.

    This backend is intentionally publish-only for the FastAPI service. Python
    parsing and AI workers should keep using Redis unless a Cloudflare Queue
    consumer worker is deployed for that specific queue.
    """

    def __init__(self, settings: Settings, queue_name: str) -> None:
        self.account_id = settings.cloudflare_account_id
        self.api_token = settings.cloudflare_api_token
        self.queue_id = settings.cloudflare_queue_id or settings.cloudflare_queue_name or queue_name
        if not self.account_id or not self.api_token or not self.queue_id:
            raise RuntimeError(
                "Cloudflare queue provider requires CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, "
                "and CLOUDFLARE_QUEUE_ID or CLOUDFLARE_QUEUE_NAME."
            )

    def push(self, message: str) -> None:
        url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/queues/{self.queue_id}/messages"
        response = httpx.post(
            url,
            headers={
                "authorization": f"Bearer {self.api_token}",
                "content-type": "application/json",
            },
            json={"body": message},
            timeout=10.0,
        )
        response.raise_for_status()

    def pop(self, timeout_seconds: int = 5) -> str | None:
        raise RuntimeError("Cloudflare Queues cannot be consumed by the Python worker. Deploy a queue consumer Worker.")
