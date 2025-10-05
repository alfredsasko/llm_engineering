"""Public façade for building and launching the week 4 exercise app."""
from __future__ import annotations

from typing import Tuple

from .config import ConfigLoader
from .executors.cpp_executor import CppExecutor
from .executors.python_executor import PythonExecutor
from .models.registry import ModelRegistry
from .prompts import PromptLoader
from .services.formatting import CodeFormatter
from .services.optimizer import CodeOptimizationService
from .ui.app import create_app


def build_app():
    """Construct and return the Gradio Blocks instance and config."""
    config = ConfigLoader().load()
    prompt_set = PromptLoader().load()
    registry = ModelRegistry(config)
    formatter = CodeFormatter()
    service = CodeOptimizationService(config, registry, prompt_set.template, formatter)
    python_executor = PythonExecutor()
    cpp_executor = CppExecutor(config.temp_dir)
    gradio_app = create_app(
        config=config,
        service=service,
        python_executor=python_executor,
        cpp_executor=cpp_executor,
        default_python=prompt_set.default_python,
    )
    return gradio_app, config


def launch() -> Tuple[object, dict]:
    """Launch the Gradio interface and return the app + launch kwargs."""
    app, config = build_app()
    launch_kwargs = {"share": False}
    launch_kwargs.update(config.launch_kwargs)
    app.launch(**launch_kwargs)
    return app, launch_kwargs


__all__ = ["build_app", "launch"]
