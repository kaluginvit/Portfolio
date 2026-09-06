"""Safe calculator tool."""

from __future__ import annotations

import logging
from typing import Any

from utils.safe_calc import SafeCalcError, safe_calculate

logger = logging.getLogger(__name__)


def calculate(expression: str) -> dict[str, Any]:
    try:
        result = safe_calculate(expression)
        return {"result": result, "expression": expression, "error": None}
    except SafeCalcError as e:
        return {"result": None, "expression": expression, "error": str(e)}


def register(mcp: Any, reg: Any) -> None:
    mcp.tool()(calculate)
    reg.register_handler("calculate", calculate)
