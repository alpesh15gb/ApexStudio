"""Base generator — shared generation utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BaseGenerator:
    """Base class for all code generators."""

    def __init__(self, workspace_path: Path):
        self.workspace_path = workspace_path

    def write_file(self, path: str, content: str) -> Path:
        """Write content to a file in the workspace."""
        full_path = self.workspace_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        logger.info(f"Generated: {path}")
        return full_path

    def file_exists(self, path: str) -> bool:
        return (self.workspace_path / path).exists()

    def get_template(self, name: str) -> str:
        """Get a template by name. Override in subclasses."""
        return ""
