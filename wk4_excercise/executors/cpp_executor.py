"""Utilities for compiling and executing generated C++ code."""
from __future__ import annotations

import subprocess
from pathlib import Path


class CppExecutor:
    """Compile and execute C++ source files using g++."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
        self._source_path = self.workspace / "optimized.cpp"
        self._binary_path = self.workspace / "optimized"

    def run(self, code: str) -> str:
        self._source_path.write_text(code, encoding="utf-8")
        compile_cmd = [
            "g++",
            "-O3",
            "-std=c++17",
            "-o",
            str(self._binary_path),
            str(self._source_path),
        ]
        run_cmd = [str(self._binary_path)]
        try:
            subprocess.run(compile_cmd, check=True, capture_output=True, text=True)
            result = subprocess.run(run_cmd, check=True, capture_output=True, text=True)
            return result.stdout
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr or "Compilation or execution failed"
            raise RuntimeError(stderr) from exc


__all__ = ["CppExecutor"]
