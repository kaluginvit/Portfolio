"""Investment project tools."""

from __future__ import annotations

import logging
from typing import Any

from services.investment_service import (
    add_investment_project as add_investment_project_svc,
    evaluate_investment as evaluate_investment_svc,
    list_investment_projects as list_investment_projects_svc,
)

logger = logging.getLogger(__name__)


def list_investment_projects() -> dict[str, Any]:
    return {"records": list_investment_projects_svc()}


def evaluate_investment(project_id: int) -> dict[str, Any]:
    return evaluate_investment_svc(project_id)


def add_investment_project(
    project_name: str,
    company_name: str,
    initial_investment: float,
    discount_rate: float,
    hurdle_rate: float,
    scenario_json: str,
    notes: str | None = None,
) -> dict[str, Any]:
    try:
        return add_investment_project_svc(
            project_name=project_name,
            company_name=company_name,
            initial_investment=initial_investment,
            discount_rate=discount_rate,
            hurdle_rate=hurdle_rate,
            scenario_json=scenario_json,
            notes=notes,
        )
    except ValueError as e:
        return {"id": None, "project_name": project_name, "company_id": None, "error": str(e)}


def register(mcp: Any, reg: Any) -> None:
    mcp.tool()(list_investment_projects)
    reg.register_handler("list_investment_projects", list_investment_projects)
    mcp.tool()(evaluate_investment)
    reg.register_handler("evaluate_investment", evaluate_investment)
    mcp.tool()(add_investment_project)
    reg.register_handler("add_investment_project", add_investment_project)
