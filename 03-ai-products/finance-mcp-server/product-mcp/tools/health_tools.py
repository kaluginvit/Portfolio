"""Health check tool."""

from __future__ import annotations

import logging
from typing import Any

from config import DB_PATH
from db import get_connection, table_counts
from schemas import tool_bundles

logger = logging.getLogger(__name__)


def health_check() -> dict[str, Any]:
    names = [b.name for b in tool_bundles()]
    with get_connection() as conn:
        counts = table_counts(conn)
    return {
        "server_status": "ok",
        "db_path": str(DB_PATH),
        "available_tools": names,
        "counts_by_table": counts,
    }


def register(mcp: Any, reg: Any) -> None:
    mcp.tool()(health_check)
    reg.register_handler("health_check", health_check)
