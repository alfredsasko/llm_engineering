"""Prompt loading and rendering utilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml


class PromptError(RuntimeError):
    """Raised when prompt assets are missing or malformed."""


@dataclass(frozen=True)
class PromptTemplate:
    """Structure for building chat prompts."""

    system: str
    user_template: str

    def build_messages(self, python_code: str) -> List[Dict[str, str]]:
        """Return messages formatted for chat-based LLMs."""
        return [
            {"role": "system", "content": self.system},
            {"role": "user", "content": self.user_template.format(python_code=python_code)},
        ]


@dataclass(frozen=True)
class PromptSet:
    template: PromptTemplate
    default_python: str


class PromptLoader:
    """Loader that reads prompts.yaml and returns strongly typed objects."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else Path(__file__).with_name("prompts.yaml")

    def load(self) -> PromptSet:
        payload = self._read_yaml()
        system = payload.get("system")
        user_template = payload.get("user_template")
        if not system or not user_template:
            raise PromptError("Prompt file must include 'system' and 'user_template' keys")

        examples = payload.get("examples") or {}
        default_python = examples.get("default_python", "")

        return PromptSet(
            template=PromptTemplate(system=system, user_template=user_template),
            default_python=default_python,
        )

    def _read_yaml(self) -> Dict[str, str]:
        if not self._path.exists():
            raise PromptError(f"Prompt file not found: {self._path}")
        with self._path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}


__all__ = ["PromptError", "PromptLoader", "PromptSet", "PromptTemplate"]
