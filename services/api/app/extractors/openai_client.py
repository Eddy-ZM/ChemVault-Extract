from __future__ import annotations

import json
from typing import Any

import httpx


class OpenAIClientError(RuntimeError):
    pass


class OpenAIStructuredOutputClient:
    def __init__(self, api_key: str, timeout_seconds: float = 90.0) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def create_structured_output(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        schema_name: str,
        json_schema: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": json_schema,
                    "strict": True,
                }
            },
        }
        response = httpx.post(
            "https://api.openai.com/v1/responses",
            headers={
                "authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise OpenAIClientError(f"OpenAI API request failed with status {response.status_code}: {response.text}")
        raw = response.json()
        text = _extract_output_text(raw)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise OpenAIClientError(f"OpenAI returned invalid JSON: {exc}") from exc
        return raw, parsed


def _extract_output_text(raw: dict[str, Any]) -> str:
    if isinstance(raw.get("output_text"), str):
        return raw["output_text"]
    for output_item in raw.get("output", []):
        for content_item in output_item.get("content", []):
            if isinstance(content_item.get("text"), str):
                return content_item["text"]
    raise OpenAIClientError("OpenAI response did not include output text.")
