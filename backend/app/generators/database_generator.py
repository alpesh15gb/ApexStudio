"""Database generator — generates SQLAlchemy models and Alembic migrations."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.generators.base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class DatabaseGenerator(BaseGenerator):
    """Generates database models and migrations from schema definitions."""

    def generate_models(self, schema: list[dict]) -> list[Path]:
        """Generate SQLAlchemy models from schema definition."""
        created = []

        models_init = ["from app.core.database import Base\n"]
        models_code = []

        for table in schema:
            table_name = table.get("name", "").lower()
            class_name = "".join(word.capitalize() for word in table_name.split("_"))

            columns_code = []
            imports = set()

            for col in table.get("columns", []):
                col_name = col["name"]
                col_type = self._map_type(col.get("type", "string"))
                col_opts = self._column_options(col)

                if col.get("foreign_key"):
                    imports.add("from sqlalchemy import ForeignKey")
                    col_opts.append(f"ForeignKey('{col['foreign_key']}')")

                columns_code.append(f"    {col_name}: Mapped[{col_type}] = mapped_column({', '.join(col_opts)})")

            if columns_code:
                model_code = f"""import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class {class_name}(Base):
    __tablename__ = "{table_name}"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
{chr(10).join(columns_code)}
"""
                models_code.append(model_code)

            models_init.append(f"from app.models.{table_name} import {class_name}")

        # Write model files
        for table in schema:
            table_name = table.get("name", "").lower()
            class_name = "".join(word.capitalize() for word in table_name.split("_"))
            # Find the matching model code
            for code in models_code:
                if f"class {class_name}" in code:
                    created.append(self.write_file(f"backend/app/models/{table_name}.py", code))
                    break

        # Write __init__
        created.append(self.write_file("backend/app/models/__init__.py", "\n".join(models_init)))

        logger.info(f"Generated {len(schema)} models")
        return created

    def _map_type(self, col_type: str) -> str:
        mapping = {
            "string": "str",
            "text": "str",
            "integer": "int",
            "float": "float",
            "boolean": "bool",
            "datetime": "datetime",
            "uuid": "uuid.UUID",
            "json": "dict",
        }
        return mapping.get(col_type.lower(), "str")

    def _column_options(self, col: dict) -> list[str]:
        opts = []
        if col.get("type", "string").lower() == "string":
            opts.append(f"String({col.get('length', 255)})")
        elif col.get("type", "string").lower() == "text":
            opts.append("Text")
        elif col.get("type", "string").lower() == "integer":
            opts.append("Integer")
        elif col.get("type", "string").lower() == "boolean":
            opts.append("Boolean, default={}".format(col.get("default", "True")))
        elif col.get("type", "string").lower() == "datetime":
            opts.append("DateTime(timezone=True), server_default=func.now()")

        if col.get("unique"):
            opts.append("unique=True")
        if col.get("nullable") is False:
            opts.append("nullable=False")
        if col.get("index"):
            opts.append("index=True")
        if col.get("default") is not None and col.get("type", "").lower() not in ("datetime",):
            opts.append(f"default={col['default']}")

        return opts
