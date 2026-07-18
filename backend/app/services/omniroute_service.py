"""Omniroute AI Gateway — multi-model routing with fallback."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OmnirouteService:
    """
    Client for the Omniroute AI gateway.
    Routes requests to the best available model (Claude, GPT, Gemini, etc.).
    Supports fallback between models.
    """

    def __init__(self):
        self.api_key = settings.omniroute_api_key
        self.base_url = settings.omniroute_base_url
        self.default_model = settings.omniroute_default_model
        self.fallback_model = settings.omniroute_fallback_model

    async def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> dict:
        """
        Send a chat completion request to the AI gateway.
        Automatically falls back on failure.
        """
        model = model or self.default_model

        # Try primary model first
        try:
            return await self._call_model(model, messages, temperature, max_tokens, stream)
        except Exception as e:
            logger.warning(f"Primary model {model} failed: {e}")

            # Try fallback model
            if self.fallback_model and model != self.fallback_model:
                try:
                    logger.info(f"Falling back to {self.fallback_model}")
                    return await self._call_model(
                        self.fallback_model, messages, temperature, max_tokens, stream
                    )
                except Exception as e2:
                    logger.error(f"Fallback model also failed: {e2}")

            return {
                "error": f"All models failed",
                "choices": [{"message": {"content": "I encountered an error processing your request."}}],
            }

    async def _call_model(
        self, model: str, messages: list[dict], temperature: float, max_tokens: int, stream: bool
    ) -> dict:
        """Call a specific model through the Omniroute gateway."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            if stream:
                return {"stream": response}  # Caller handles streaming

            result = response.json()
            logger.info(f"Omniroute: model={model}, tokens={result.get('usage', {})}")
            return result

    async def get_response(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
    ) -> str:
        """Simple helper to get a text response."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        result = await self.chat_completion(messages, model=model)

        if "error" in result:
            return result["error"]

        try:
            return result["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return "I received an unexpected response format."

    async def stream_response(
        self,
        system_prompt: str,
        user_message: str,
        model: str | None = None,
    ):
        """Stream a response from the AI model."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model or self.default_model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 4096,
                        "stream": True,
                    },
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                logger.error(f"Stream error: {e}")
                yield f"\n[Error: {e}]"
