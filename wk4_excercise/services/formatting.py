"""Utilities for post-processing LLM responses into compilable C++."""
from __future__ import annotations


class CodeFormatter:
    """Extracts C++ code blocks from model responses."""

    def __init__(self, language: str = "cpp") -> None:
        self.language = language

    def sanitize(self, text: str) -> str:
        """Return the best-effort extraction of the target language code block."""
        fence = f"```{self.language}"
        if fence in text:
            start = text.find(fence) + len(fence)
            end = text.find("```", start)
            if end == -1:
                return text[start:].strip()
            return text[start:end].strip()
        if "```" in text:
            start = text.find("```") + len("```")
            end = text.find("```", start)
            if end == -1:
                return text[start:].strip()
            return text[start:end].strip()
        return text.strip()

    def strip_fences(self, text: str) -> str:
        """Remove code fences without attempting to extract a block."""
        fence = f"```{self.language}"
        cleaned = text.replace(fence, "")
        return cleaned.replace("```", "").strip()


__all__ = ["CodeFormatter"]
