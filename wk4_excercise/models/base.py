"""Model client abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from ..config import ModelConfig
from ..prompts import PromptTemplate


class ModelClientError(RuntimeError):
    """Raised when a model client cannot fulfill a request."""


class BaseModelClient(ABC):
    """Abstract base class for all model providers."""

    def __init__(self, config: ModelConfig) -> None:
        self.config = config

    @abstractmethod
    def stream_code(self, python_code: str, prompt: PromptTemplate) -> Iterable[str]:
        """Yield chunks of generated C++ code for the supplied Python input."""

    def _ensure_api_key(self) -> str:
        """Fetch the API key from environment variables, raising if missing."""
        if not self.config.api_key_env:
            raise ModelClientError(
                f"Model '{self.config.name}' does not define api_key_env in config.yaml"
            )
        import os

        api_key = os.environ.get(self.config.api_key_env)
        if not api_key:
            raise ModelClientError(
                f"Environment variable {self.config.api_key_env} is required for model "
                f"'{self.config.name}'."
            )
        return api_key


__all__ = ["BaseModelClient", "ModelClientError"]
