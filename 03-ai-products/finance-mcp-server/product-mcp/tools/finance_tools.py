"""Financial listing, KPIs, plan vs fact, search."""

from __future__ import annotations

import logging
from typing import Any

from services.finance_service import (
    calculate_kpis as calculate_kpis_svc,
    find_records as find_records_svc,
    list_budget_records as list_budget_records_svc,
    list_companies as list_companies_svc,
    list_financial_records as list_financial_records_svc,
    plan_vs_fact as plan_vs_fact_svc,
)
from utils.helpers import plan_vs_fact_value_error, records_value_error

logger = logging.getLogger(__name__)


def list_companies() -> dict[str, Any]:
    return {"companies": list_companies_svc()}


def list_financial_records(
    statement_type: str | None = None,
    company_name: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
    department: str | None = None,
    project: str | None = None,
    counterparty: str | None = None,
) -> dict[str, Any]:
    try:
        rows = list_financial_records_svc(
            statement_type=statement_type,
            company_name=company_name,
            start_date=start_date,
            end_date=end_date,
            category=category,
            department=department,
            project=project,
            counterparty=counterparty,
        )
        return {"records": rows}
    except ValueError as e:
        return records_value_error(e)


def list_budget_records(
    company_name: str | None = None,
    version: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    try:
        rows = list_budget_records_svc(
            company_name=company_name,
            version=version,
            start_date=start_date,
            end_date=end_date,
            category=category,
        )
        return {"records": rows}
    except ValueError as e:
        return records_value_error(e)


def calculate_kpis(
    period_start: str | None = None,
    period_end: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    try:
        return calculate_kpis_svc(period_start, period_end, company_name)
    except ValueError as e:
        return {"error": str(e)}


def plan_vs_fact(
    period_start: str | None = None,
    period_end: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    try:
        return plan_vs_fact_svc(period_start, period_end, company_name)
    except ValueError as e:
        return plan_vs_fact_value_error(e)


def find_records(query: str) -> dict[str, Any]:
    return {"records": find_records_svc(query)}


def register(mcp: Any, reg: Any) -> None:
    mcp.tool()(list_companies)
    reg.register_handler("list_companies", list_companies)
    mcp.tool()(list_financial_records)
    reg.register_handler("list_financial_records", list_financial_records)
    mcp.tool()(list_budget_records)
    reg.register_handler("list_budget_records", list_budget_records)
    mcp.tool()(calculate_kpis)
    reg.register_handler("calculate_kpis", calculate_kpis)
    mcp.tool()(plan_vs_fact)
    reg.register_handler("plan_vs_fact", plan_vs_fact)
    mcp.tool()(find_records)
    reg.register_handler("find_records", find_records)
