"""Model registry and factory helpers."""
from __future__ import annotations

from typing import Dict

from ..config import AppConfig, ModelConfig
from .base import BaseModelClient, ModelClientError


class ModelRegistry:
    """Creates and caches model clients based on configuration."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._instances: Dict[str, BaseModelClient] = {}

    def get(self, model_name: str) -> BaseModelClient:
        """Return (and cache) a client instance for the requested model."""

        if model_name not in self._config.models:
            raise ModelClientError(f"Unknown model '{model_name}' requested")
        if model_name not in self._instances:
            self._instances[model_name] = self._create_client(self._config.models[model_name])
        return self._instances[model_name]

    def list_choices(self) -> Dict[str, str]:
        """Expose model names mapped to human-readable labels."""

        return self._config.model_choices()

    def _create_client(self, config: ModelConfig) -> BaseModelClient:
        provider = config.provider.lower()
        if provider == "openai":
            from .openai_client import OpenAIModelClient

            return OpenAIModelClient(config)
        if provider == "anthropic":
            from .anthropic_client import AnthropicModelClient

            return AnthropicModelClient(config)
        if provider == "huggingface":
            from .huggingface_client import HuggingFaceModelClient

            return HuggingFaceModelClient(config)
        if provider == "google-ai":
            from .gemini_client import GeminiModelClient

            return GeminiModelClient(config)
        raise ModelClientError(f"Unsupported provider '{config.provider}'")


__all__ = ["ModelRegistry"]
