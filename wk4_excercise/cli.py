"""Command-line interface for the Python to C++ optimizer."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

try:  # pragma: no cover - optional dependency guard
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv(*args, **kwargs):  # type: ignore[no-redef]
        return False

from .app import build_app, launch
from .config import ConfigLoader
from .models.registry import ModelRegistry
from .prompts import PromptLoader
from .services.formatting import CodeFormatter
from .services.optimizer import CodeOptimizationService


def _load_env(path: Optional[Path]) -> None:
    """Load environment variables from a .env file if present."""
    if path is None:
        load_dotenv(override=True)
    else:
        load_dotenv(path, override=True)


def _build_service() -> CodeOptimizationService:
    config = ConfigLoader().load()
    prompt_set = PromptLoader().load()
    registry = ModelRegistry(config)
    return CodeOptimizationService(config, registry, prompt_set.template, CodeFormatter())


def _optimize_file(python_path: Path, model: Optional[str]) -> str:
    service = _build_service()
    source = python_path.read_text(encoding="utf-8")
    target_model = model or service.default_model
    return service.optimize_once(source, target_model)


def _optimize_stream(model: Optional[str]) -> str:
    service = _build_service()
    python_code = sys.stdin.read()
    target_model = model or service.default_model
    last_chunk = ""
    for chunk in service.stream_optimized_code(python_code, target_model):
        last_chunk = chunk
    return last_chunk


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Python to C++ optimizer supporting both CLI and Gradio UI modes",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Path to .env file with API keys (defaults to loading .env from cwd)",
    )
    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser("serve", help="Launch the Gradio web UI")
    serve_parser.add_argument(
        "--share",
        action="store_true",
        help="Enable public Gradio sharing when launching the app",
    )

    file_parser = subparsers.add_parser("optimize", help="Convert a Python file to C++ and print it")
    file_parser.add_argument("path", type=Path, help="Path to the Python file")
    file_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override the configured default model",
    )

    stream_parser = subparsers.add_parser(
        "stream", help="Read Python code from stdin and stream converted C++ to stdout"
    )
    stream_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override the configured default model",
    )

    args = parser.parse_args(argv)
    _load_env(args.env_file)

    if args.command == "serve":
        app, config = build_app()
        launch_kwargs = config.launch_kwargs.copy()
        if args.share:
            launch_kwargs["share"] = True
        app.launch(**launch_kwargs)
        return 0

    if args.command == "optimize":
        result = _optimize_file(args.path, args.model)
        sys.stdout.write(result + "\n")
        return 0

    if args.command == "stream":
        result = _optimize_stream(args.model)
        sys.stdout.write(result + "\n")
        return 0

    launch()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
