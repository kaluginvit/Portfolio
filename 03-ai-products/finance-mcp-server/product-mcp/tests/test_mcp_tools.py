"""
Интеграционные тесты для finance-mcp-server (portfolio smoke suite).

Проверяет:
- БД создаётся и seed-данные загружаются (idempotent — двойной запуск не ломается)
- 5 ключевых tools возвращают непустой, ожидаемый результат
- Использует реальную SQLite в tempdir через фикстуру mcp_env из conftest.py
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Шаг 1 — База создаётся и seed idempotent
# ---------------------------------------------------------------------------


def test_db_created_and_seeded(mcp_env) -> None:
    """SQLite-файл существует и содержит seed-записи."""
    assert mcp_env.db_path.is_file(), "DB-файл должен быть создан"

    raw = mcp_env.dispatch("health_check", {})
    assert raw["success"] is True
    counts = raw["result"]["counts_by_table"]
    assert counts["companies"] >= 2
    assert counts["financial_records"] >= 50
    assert counts["contracts"] >= 1
    assert counts["investment_projects"] >= 1


def test_seed_is_idempotent(mcp_env) -> None:
    """Повторный вызов seed_if_empty не добавляет дубликаты компаний."""
    import seed

    before = mcp_env.dispatch("list_companies", {})
    count_before = len(before["result"]["companies"])

    seed.seed_if_empty()  # второй вызов — должен пропустить

    after = mcp_env.dispatch("list_companies", {})
    count_after = len(after["result"]["companies"])

    assert count_before == count_after, (
        f"Seed добавил лишние компании при повторном вызове: "
        f"до={count_before}, после={count_after}"
    )


# ---------------------------------------------------------------------------
# Шаг 2 — 5 ключевых tools возвращают непустой результат
# ---------------------------------------------------------------------------


def test_tool_list_companies(mcp_env) -> None:
    """list_companies возвращает как минимум двух сидовых контрагентов."""
    raw = mcp_env.dispatch("list_companies", {})
    assert raw["success"] is True
    companies = raw["result"]["companies"]
    assert len(companies) >= 2
    names = {c["name"] for c in companies}
    assert "Demo Holdings OÜ" in names
    assert "Subsidiary LLC" in names


def test_tool_calculate_kpis(mcp_env) -> None:
    """calculate_kpis возвращает ненулевую выручку и EBITDA за 2024."""
    raw = mcp_env.dispatch(
        "calculate_kpis",
        {
            "company_name": "Demo Holdings OÜ",
            "period_start": "2024-01-01",
            "period_end": "2024-12-31",
        },
    )
    assert raw["success"] is True
    result = raw["result"]
    assert "error" not in result or result.get("error") is None
    assert result["total_revenue"] > 0, "Выручка должна быть > 0"
    assert result["ebitda"] != 0, "EBITDA должен быть ненулевым"
    assert isinstance(result.get("ebitda_margin"), float)


def test_tool_list_financial_records(mcp_env) -> None:
    """list_financial_records с фильтром по типу pnl возвращает записи."""
    raw = mcp_env.dispatch(
        "list_financial_records",
        {
            "statement_type": "pnl",
            "company_name": "Demo Holdings OÜ",
        },
    )
    assert raw["success"] is True
    records = raw["result"]["records"]
    assert len(records) > 0, "P&L-записи должны присутствовать"
    # Все записи должны быть правильного типа
    for r in records:
        assert r["statement_type"] == "pnl"


def test_tool_list_contracts(mcp_env) -> None:
    """list_contracts возвращает сидовые договоры."""
    raw = mcp_env.dispatch("list_contracts", {})
    assert raw["success"] is True
    contracts = raw["result"]["records"]
    assert len(contracts) >= 1
    # Каждый договор должен иметь поле contract_name
    for c in contracts:
        assert "contract_name" in c


def test_tool_evaluate_investment(mcp_env) -> None:
    """evaluate_investment для project_id=1 возвращает NPV и IRR."""
    raw = mcp_env.dispatch("evaluate_investment", {"project_id": 1})
    assert raw["success"] is True
    result = raw["result"]
    assert "npv" in result, "Результат должен содержать npv"
    assert "irr" in result, "Результат должен содержать irr"
    assert isinstance(result["npv"], (int, float))


def test_tool_calculate_safe_expr(mcp_env) -> None:
    """calculate выполняет безопасные арифметические выражения."""
    raw = mcp_env.dispatch("calculate", {"expression": "850000 * 0.42 + 210000"})
    assert raw["success"] is True
    result = raw["result"]
    assert result["error"] is None
    assert abs(result["result"] - (850000 * 0.42 + 210000)) < 1e-6


def test_tool_calculate_division_by_zero(mcp_env) -> None:
    """calculate корректно обрабатывает деление на ноль — возвращает ошибку, не падает."""
    raw = mcp_env.dispatch("calculate", {"expression": "100 / 0"})
    assert raw["success"] is True  # tool не падает
    result = raw["result"]
    assert result["error"] is not None, "Должна быть ошибка при делении на ноль"
    assert result["result"] is None
