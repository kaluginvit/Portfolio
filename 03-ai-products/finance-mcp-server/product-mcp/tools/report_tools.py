"""Treasury, calendar, export tools."""

from __future__ import annotations

import logging
from typing import Any

from services.reporting_service import export_report as export_report_svc

logger = logging.getLogger(__name__)
from services.treasury_service import (
    liquidity_forecast as liquidity_forecast_svc,
    list_cash_positions as list_cash_positions_svc,
    payment_calendar as payment_calendar_svc,
)
from utils.helpers import (
    export_report_value_error,
    liquidity_forecast_value_error,
    records_value_error,
)


def list_cash_positions(company_name: str | None = None, position_date: str | None = None) -> dict[str, Any]:
    try:
        return {"records": list_cash_positions_svc(company_name, position_date)}
    except ValueError as e:
        return records_value_error(e)


def liquidity_forecast(days: int = 90, company_name: str | None = None) -> dict[str, Any]:
    try:
        return liquidity_forecast_svc(days, company_name)
    except ValueError as e:
        return liquidity_forecast_value_error(e)


def payment_calendar(
    start_date: str | None = None,
    end_date: str | None = None,
    company_name: str | None = None,
) -> dict[str, Any]:
    try:
        return {"records": payment_calendar_svc(start_date, end_date, company_name)}
    except ValueError as e:
        return records_value_error(e)


def export_report(
    report_type: str,
    output_format: str | None = "json",
    output_path: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    company_name: str | None = None,
    liquidity_days: int | None = 90,
    payment_start: str | None = None,
    payment_end: str | None = None,
    project_id: int | None = None,
) -> dict[str, Any]:
    try:
        return export_report_svc(
            report_type,
            output_format,
            output_path,
            period_start=period_start,
            period_end=period_end,
            company_name=company_name,
            liquidity_days=liquidity_days or 90,
            payment_start=payment_start,
            payment_end=payment_end,
            project_id=project_id,
        )
    except ValueError as e:
        return export_report_value_error(report_type, e)


def register(mcp: Any, reg: Any) -> None:
    mcp.tool()(list_cash_positions)
    reg.register_handler("list_cash_positions", list_cash_positions)
    mcp.tool()(liquidity_forecast)
    reg.register_handler("liquidity_forecast", liquidity_forecast)
    mcp.tool()(payment_calendar)
    reg.register_handler("payment_calendar", payment_calendar)
    mcp.tool()(export_report)
    reg.register_handler("export_report", export_report)
