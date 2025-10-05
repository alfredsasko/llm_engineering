"""Service layer orchestrating model calls and post-processing."""
from __future__ import annotations

from typing import Generator

from ..prompts import PromptTemplate
from ..config import AppConfig
from ..models.registry import ModelRegistry
from .formatting import CodeFormatter


class CodeOptimizationService:
    """High-level façade for converting Python code into optimized C++."""

    def __init__(
        self,
        config: AppConfig,
        registry: ModelRegistry,
        prompt_template: PromptTemplate,
        formatter: CodeFormatter | None = None,
    ) -> None:
        self._config = config
        self._registry = registry
        self._prompt_template = prompt_template
        self._formatter = formatter or CodeFormatter()

    @property
    def default_model(self) -> str:
        return self._config.default_model

    def stream_optimized_code(self, python_code: str, model_name: str) -> Generator[str, None, None]:
        client = self._registry.get(model_name)
        aggregated = ""
        for fragment in client.stream_code(python_code, self._prompt_template):
            aggregated += fragment
            yield self._formatter.sanitize(aggregated)

    def optimize_once(self, python_code: str, model_name: str) -> str:
        client = self._registry.get(model_name)
        aggregated = "".join(client.stream_code(python_code, self._prompt_template))
        return self._formatter.sanitize(aggregated)


__all__ = ["CodeOptimizationService"]
