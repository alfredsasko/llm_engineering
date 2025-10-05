"""Configuration loading utilities for the week 4 exercise package."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigError(RuntimeError):
    """Raised when the application configuration cannot be loaded or validated."""


@dataclass(frozen=True)
class ModelConfig:
    """Immutable configuration describing a single model backend."""

    name: str
    display_name: str
    provider: str
    model_id: str
    api_key_env: str | None = None
    endpoint: str | None = None
    generation_kwargs: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    """Immutable application configuration."""

    title: str
    default_model: str
    temp_dir: Path
    css_path: Path | None
    launch_kwargs: Dict[str, Any]
    models: Dict[str, ModelConfig]

    def model_choices(self) -> Dict[str, str]:
        """Return mapping of model name to display name for UI consumption."""
        return {name: cfg.display_name for name, cfg in self.models.items()}


class ConfigLoader:
    """Loader responsible for turning YAML configuration into strongly typed objects."""

    def __init__(self, path: str | Path | None = None) -> None:
        self._path = Path(path) if path else Path(__file__).with_name("config.yaml")

    def load(self) -> AppConfig:
        raw = self._read_yaml()
        app_section = raw.get("app") or {}
        models_section = raw.get("models") or {}
        if not models_section:
            raise ConfigError("No models configured. Update config.yaml")

        css_path = app_section.get("css_path")
        css = (self._path.parent / css_path) if css_path else None
        if css and not css.exists():
            raise ConfigError(f"CSS path does not exist: {css}")

        temp_dir = app_section.get("temp_dir", "wk4_excercise/runtime")
        temp_dir_path = (self._path.parent / temp_dir).resolve()
        temp_dir_path.mkdir(parents=True, exist_ok=True)

        models: Dict[str, ModelConfig] = {}
        for name, payload in models_section.items():
            models[name] = ModelConfig(
                name=name,
                display_name=payload.get("display_name", name),
                provider=payload.get("provider", ""),
                model_id=payload.get("model_id", ""),
                api_key_env=payload.get("api_key_env"),
                endpoint=payload.get("endpoint"),
                generation_kwargs=payload.get("generation_kwargs", {}),
            )
            if not models[name].provider:
                raise ConfigError(f"Model '{name}' is missing provider in config.yaml")
            if not models[name].model_id:
                raise ConfigError(f"Model '{name}' is missing model_id in config.yaml")

        default_model = app_section.get("default_model")
        if not default_model:
            raise ConfigError("Default model must be specified under app.default_model")
        if default_model not in models:
            raise ConfigError(f"Default model '{default_model}' not found in models section")

        launch_kwargs = app_section.get("launch", {})
        title = app_section.get("title", "Code Optimizer")

        return AppConfig(
            title=title,
            default_model=default_model,
            temp_dir=temp_dir_path,
            css_path=css,
            launch_kwargs=launch_kwargs,
            models=models,
        )

    def _read_yaml(self) -> Dict[str, Any]:
        if not self._path.exists():
            raise ConfigError(f"Configuration file not found: {self._path}")
        with self._path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}


__all__ = ["AppConfig", "ConfigError", "ConfigLoader", "ModelConfig"]
