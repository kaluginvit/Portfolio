"""Import-related MCP tools."""

from __future__ import annotations

import logging
from typing import Any

from services.contract_service import import_contract as import_contract_svc
from services.import_service import import_csv as import_csv_svc

logger = logging.getLogger(__name__)


def import_csv(
    file_path: str,
    statement_type: str,
    company_name: str | None = None,
    version: str | None = None,
) -> dict[str, Any]:
    return import_csv_svc(file_path, statement_type, company_name, version)


def import_contract(file_path: str) -> dict[str, Any]:
    return import_contract_svc(file_path)


def register(mcp: Any, reg: Any) -> None:
    mcp.tool()(import_csv)
    reg.register_handler("import_csv", import_csv)
    mcp.tool()(import_contract)
    reg.register_handler("import_contract", import_contract)
