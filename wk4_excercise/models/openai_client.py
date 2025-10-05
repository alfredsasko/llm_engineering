"""OpenAI model client implementation."""
from __future__ import annotations

from typing import Iterable

from openai import OpenAI

from .base import BaseModelClient
from ..prompts import PromptTemplate


class OpenAIModelClient(BaseModelClient):
    """Stream completions from OpenAI's Chat Completions API."""

    def __init__(self, config) -> None:  # type: ignore[override]
        super().__init__(config)
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            api_key = self._ensure_api_key()
            self._client = OpenAI(api_key=api_key)
        return self._client

    def stream_code(self, python_code: str, prompt: PromptTemplate) -> Iterable[str]:  # type: ignore[override]
        messages = prompt.build_messages(python_code)
        stream = self._get_client().chat.completions.create(
            model=self.config.model_id,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            fragment = chunk.choices[0].delta.content or ""
            if fragment:
                yield fragment


__all__ = ["OpenAIModelClient"]
