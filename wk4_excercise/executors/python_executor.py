"""Utilities for executing user-provided Python code safely."""
from __future__ import annotations

import contextlib
import io
import traceback


class PythonExecutor:
    """Executes Python code and captures stdout and exceptions."""

    def run(self, code: str) -> str:
        stdout_buf = io.StringIO()
        globals_ns = {}
        try:
            compiled = compile(code, "<user_code>", "exec")
            with contextlib.redirect_stdout(stdout_buf):
                exec(compiled, globals_ns, globals_ns)
        except Exception:
            stdout_buf.write(traceback.format_exc())
        return stdout_buf.getvalue()


__all__ = ["PythonExecutor"]
