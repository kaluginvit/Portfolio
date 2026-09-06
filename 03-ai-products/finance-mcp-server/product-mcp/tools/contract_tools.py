"""Contract listing and risk scan."""

from __future__ import annotations

import logging
from typing import Any

from services.contract_service import contract_risk_scan as contract_risk_scan_svc
from services.contract_service import list_contracts as list_contracts_svc

logger = logging.getLogger(__name__)


def list_contracts(active_only: bool = False) -> dict[str, Any]:
    return {"records": list_contracts_svc(active_only=active_only)}


def contract_risk_scan() -> dict[str, Any]:
    return contract_risk_scan_svc()


def register(mcp: Any, reg: Any) -> None:
    mcp.tool()(list_contracts)
    reg.register_handler("list_contracts", list_contracts)
    mcp.tool()(contract_risk_scan)
    reg.register_handler("contract_risk_scan", contract_risk_scan)
