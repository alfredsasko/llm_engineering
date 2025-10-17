"""Gradio user interface for the optimizer."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import gradio as gr

from ..config import AppConfig
from ..executors.cpp_executor import CppExecutor
from ..executors.python_executor import PythonExecutor
from ..services.optimizer import CodeOptimizationService


def _load_css(path: Path | None) -> str | None:
    """Return the CSS contents if the optional path exists."""

    if not path:
        return None
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def create_app(
    config: AppConfig,
    service: CodeOptimizationService,
    python_executor: PythonExecutor,
    cpp_executor: CppExecutor,
    default_python: str,
) -> gr.Blocks:
    """Build and return the configured Gradio Blocks interface."""

    css = _load_css(config.css_path)
    model_choices: Dict[str, str] = config.model_choices()

    def convert_handler(python_code: str, model_name: str):
        yield from service.stream_optimized_code(python_code, model_name)

    def python_handler(python_code: str) -> str:
        return python_executor.run(python_code)

    def cpp_handler(cpp_code: str) -> str:
        return cpp_executor.run(cpp_code)

    with gr.Blocks(css=css, title=config.title) as demo:
        gr.Markdown(f"## {config.title}")
        with gr.Row():
            python_box = gr.Textbox(label="Python code", value=default_python, lines=12)
            cpp_box = gr.Textbox(label="C++ code", lines=12)
        with gr.Row():
            model_dropdown = gr.Dropdown(
                label="Model",
                choices=list(model_choices.keys()),
                value=service.default_model,
                interactive=True,
            )
            convert_button = gr.Button("Convert to C++")
            clear_button = gr.Button("Clear")
        with gr.Row():
            python_run = gr.Button("Run Python")
            cpp_run = gr.Button("Run C++")
        with gr.Row():
            python_output = gr.TextArea(label="Python output", elem_classes=["python-output"])
            cpp_output = gr.TextArea(label="C++ output", elem_classes=["cpp-output"])

        convert_button.click(
            convert_handler,
            inputs=[python_box, model_dropdown],
            outputs=cpp_box,
        )
        clear_button.click(
            lambda: (default_python, ""),
            inputs=None,
            outputs=[python_box, cpp_box],
        )
        python_run.click(python_handler, inputs=python_box, outputs=python_output)
        cpp_run.click(cpp_handler, inputs=cpp_box, outputs=cpp_output)

    return demo


__all__ = ["create_app"]
