"""Google Gemini model client implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseModelClient, ModelClientError
from ..prompts import PromptTemplate


class GeminiModelClient(BaseModelClient):
    """Client for streaming code generation from Google Gemini."""

    def __init__(self, config) -> None:  # type: ignore[override]
        super().__init__(config)
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover - handled at runtime
            raise ModelClientError(
                "google-generativeai package is required for Gemini models"
            ) from exc

        api_key = self._ensure_api_key()
        genai.configure(api_key=api_key)
        self._genai = genai

    def stream_code(self, python_code: str, prompt: PromptTemplate) -> Iterable[str]:  # type: ignore[override]
        messages = prompt.build_messages(python_code)
        system_text = messages[0]["content"]
        user_text = messages[1]["content"]
        model = self._genai.GenerativeModel(
            model_name=self.config.model_id,
            system_instruction=system_text,
        )
        response = model.generate_content(user_text, stream=True)
        for chunk in response:
            text = getattr(chunk, "text", None)
            if text:
                yield text


__all__ = ["GeminiModelClient"]
