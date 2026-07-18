"""Error analyzer — parses build logs and identifies root causes."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ErrorAnalyzer:
    """
    Analyzes build errors and stack traces to identify root causes.
    Used by the Build Agent and Debug Agent for auto-fix.
    """

    COMMON_PATTERNS: list[dict[str, Any]] = [
        {
            "pattern": r"ModuleNotFoundError: No module named '(\w+)'",
            "type": "missing_module",
            "severity": "high",
            "message": "Missing Python module: {0}",
            "fix": "pip install {0}",
        },
        {
            "pattern": r"ImportError: cannot import name '(\w+)' from '(\w+)'",
            "type": "import_error",
            "severity": "high",
            "message": "Import error: {0} from {1}",
        },
        {
            "pattern": r"SyntaxError: (.+)",
            "type": "syntax_error",
            "severity": "critical",
            "message": "Syntax error: {0}",
        },
        {
            "pattern": r"IndentationError: (.+)",
            "type": "indentation_error",
            "severity": "critical",
            "message": "Indentation error: {0}",
        },
        {
            "pattern": r"relation \"(\w+)\" does not exist",
            "type": "missing_table",
            "severity": "high",
            "message": "Database table missing: {0}",
            "fix": "Run database migrations",
        },
        {
            "pattern": r"column (\w+) does not exist",
            "type": "missing_column",
            "severity": "high",
            "message": "Database column missing: {0}",
            "fix": "Run database migrations",
        },
        {
            "pattern": r"KeyError: '(\w+)'",
            "type": "key_error",
            "severity": "medium",
            "message": "Missing key: {0}",
        },
        {
            "pattern": r"TypeError: (.+)",
            "type": "type_error",
            "severity": "high",
            "message": "Type error: {0}",
        },
        {
            "pattern": r"AttributeError: (.+)",
            "type": "attribute_error",
            "severity": "high",
            "message": "Attribute error: {0}",
        },
        {
            "pattern": r"NameError: name '(\w+)' is not defined",
            "type": "name_error",
            "severity": "high",
            "message": "Undefined name: {0}",
        },
        {
            "pattern": r"ValueError: (.+)",
            "type": "value_error",
            "severity": "medium",
            "message": "Value error: {0}",
        },
        {
            "pattern": r"docker:.*not found",
            "type": "docker_not_found",
            "severity": "critical",
            "message": "Docker command not found",
        },
        {
            "pattern": r"port is already allocated",
            "type": "port_conflict",
            "severity": "medium",
            "message": "Port already in use",
        },
        {
            "pattern": r"Container (.+) is not running",
            "type": "container_not_running",
            "severity": "medium",
            "message": "Container {0} not running",
        },
        {
            "pattern": r"Error: (.+)",
            "type": "generic_error",
            "severity": "low",
            "message": "Error: {0}",
        },
    ]

    FIX_STRATEGIES: dict[str, str] = {
        "missing_module": "Install the missing Python module",
        "missing_table": "Run alembic upgrade head",
        "missing_column": "Run alembic upgrade head",
        "syntax_error": "Fix the syntax error in the specified file",
        "indentation_error": "Fix indentation in the specified file",
        "port_conflict": "Stop conflicting container or change port",
        "container_not_running": "Start the container",
    }

    @classmethod
    def analyze(cls, logs: str) -> list[dict[str, Any]]:
        """
        Analyze build logs and return a list of identified errors.
        """
        findings = []

        for error_def in cls.COMMON_PATTERNS:
            matches = re.finditer(error_def["pattern"], logs, re.MULTILINE)
            for match in matches:
                error = {
                    "type": error_def["type"],
                    "severity": error_def["severity"],
                    "message": error_def["message"].format(*match.groups()) if match.groups() else error_def["message"],
                    "fix": error_def.get("fix"),
                    "line": cls._extract_line_number(logs, match.start()),
                }
                findings.append(error)

        return findings

    @classmethod
    def get_fix_suggestion(cls, error_type: str) -> str | None:
        """Get a fix suggestion for an error type."""
        return cls.FIX_STRATEGIES.get(error_type)

    @staticmethod
    def _extract_line_number(logs: str, position: int) -> int | None:
        """Extract the line number from a position in the log."""
        before = logs[:position]
        return before.count("\n") + 1

    @staticmethod
    def get_error_summary(logs: str, max_length: int = 500) -> str:
        """Get a concise error summary from build logs."""
        # Find traceback blocks
        traceback_pattern = r"Traceback \(most recent call last\).+?\n(\w+Error: .+)"
        matches = re.findall(traceback_pattern, logs, re.DOTALL)

        if matches:
            summary = "\n".join(m[-200:] for m in matches[-3:])
            return summary[:max_length]

        # Fallback: return last portion of logs
        return logs[-max_length:]
