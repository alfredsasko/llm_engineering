"""Sphinx configuration for the wk4_excercise package."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

project = "Python code optimizer to C++"
author = "Alfred Sasko"
year = datetime.now().year
copyright = f"{year}, {author}"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

autodoc_typehints = "description"
autodoc_mock_imports = [
    "anthropic",
    "google.generativeai",
    "huggingface_hub",
    "openai",
    "transformers",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

html_theme = "alabaster"
html_static_path = ["_static"]
