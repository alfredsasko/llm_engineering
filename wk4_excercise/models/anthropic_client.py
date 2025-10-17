"""Anthropic Claude model client implementation."""
from __future__ import annotations

from typing import Iterable

import anthropic

from .base import BaseModelClient
from ..prompts import PromptTemplate


class AnthropicModelClient(BaseModelClient):
    """Stream code suggestions from Anthropic Claude."""

    def __init__(self, config) -> None:  # type: ignore[override]
        super().__init__(config)
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            api_key = self._ensure_api_key()
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def stream_code(self, python_code: str, prompt: PromptTemplate) -> Iterable[str]:  # type: ignore[override]
        """Yield response fragments from an Anthropic streaming session."""

        messages = prompt.build_messages(python_code)
        system_text = messages[0]["content"]
        user_message = messages[1]["content"]
        stream = self._get_client().messages.stream(
            model=self.config.model_id,
            system=system_text,
            max_tokens=4096,
            messages=[{"role": "user", "content": user_message}],
        )
        with stream as events:
            for text in events.text_stream:
                if text:
                    yield text


__all__ = ["AnthropicModelClient"]
