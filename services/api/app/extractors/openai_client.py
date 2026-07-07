from __future__ import annotations

import json
import re
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
        parsed = _parse_json_text(text, provider_name="OpenAI")
        return raw, parsed


class DeepSeekStructuredOutputClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", timeout_seconds: float = 90.0) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
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
        schema_prompt = (
            f"Return only a JSON object named {schema_name} that conforms to this JSON Schema. "
            "Do not include markdown fences, comments, or explanatory text.\n\n"
            f"{json.dumps(json_schema, ensure_ascii=False)}"
        )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": f"{system_prompt}\n\n{schema_prompt}"},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "stream": False,
        }
        response = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={
                "authorization": f"Bearer {self.api_key}",
                "content-type": "application/json",
            },
            json=payload,
            timeout=self.timeout_seconds,
        )
        if response.status_code >= 400:
            raise OpenAIClientError(f"DeepSeek API request failed with status {response.status_code}: {response.text}")
        raw = response.json()
        text = _extract_chat_completion_text(raw, provider_name="DeepSeek")
        parsed = _parse_json_text(text, provider_name="DeepSeek")
        return raw, parsed


def _extract_output_text(raw: dict[str, Any]) -> str:
    if isinstance(raw.get("output_text"), str):
        return raw["output_text"]
    for output_item in raw.get("output", []):
        for content_item in output_item.get("content", []):
            if isinstance(content_item.get("text"), str):
                return content_item["text"]
    raise OpenAIClientError("OpenAI response did not include output text.")


def _extract_chat_completion_text(raw: dict[str, Any], *, provider_name: str) -> str:
    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenAIClientError(f"{provider_name} response did not include choices.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    raise OpenAIClientError(f"{provider_name} response did not include message content.")


def _parse_json_text(text: str, *, provider_name: str) -> dict[str, Any]:
    cleaned = _strip_json_fence(text.strip())
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise OpenAIClientError(f"{provider_name} returned invalid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise OpenAIClientError(f"{provider_name} returned JSON that is not an object.")
    return parsed


def _strip_json_fence(text: str) -> str:
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else text
