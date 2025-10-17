"""Hugging Face Inference API client implementation."""
from __future__ import annotations

from typing import Iterable

from .base import BaseModelClient, ModelClientError
from ..prompts import PromptTemplate


class HuggingFaceModelClient(BaseModelClient):
    """Client for streaming code generation from Hugging Face text-generation endpoints."""

    def __init__(self, config) -> None:  # type: ignore[override]
        super().__init__(config)
        if not config.endpoint:
            raise ModelClientError(
                f"Model '{config.name}' must define an endpoint for Hugging Face inference"
            )
        try:
            from huggingface_hub import InferenceClient
            from transformers import AutoTokenizer
        except ImportError as exc:  # pragma: no cover - handled at runtime
            raise ModelClientError(
                "huggingface-hub and transformers packages are required for Hugging Face models"
            ) from exc

        token = self._ensure_api_key()
        self._tokenizer = AutoTokenizer.from_pretrained(config.model_id)
        self._client = InferenceClient(config.endpoint, token=token)
        self._generation_kwargs = {"stream": True}
        self._generation_kwargs.update(config.generation_kwargs)

    def stream_code(self, python_code: str, prompt: PromptTemplate) -> Iterable[str]:  # type: ignore[override]
        """Yield response fragments from the Hugging Face inference endpoint."""

        messages = prompt.build_messages(python_code)
        text_prompt = self._tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        stream = self._client.text_generation(text_prompt, **self._generation_kwargs)
        for event in stream:
            if hasattr(event, "token") and event.token and event.token.text:
                yield event.token.text
            elif isinstance(event, str):
                yield event


__all__ = ["HuggingFaceModelClient"]
