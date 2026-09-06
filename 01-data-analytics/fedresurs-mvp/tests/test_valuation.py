"""
tests/test_valuation.py — тесты ключевой бизнес-логики оценки лотов.

Проверяются функции без реального парсинга и без обращений к API.
Запуск: python -m pytest tests/ -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Добавляем корень проекта в sys.path, чтобы импортировать модули без установки пакета
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ── Импорты из основных модулей ────────────────────────────────────────────

from valuate import (
    _extract_json,
    build_prompt,
    clean_description,
    format_search_results,
)
from fedresurs_mvp import (
    classify_asset,
    clean_result_url,
    extract_price,
    extract_price_per_m2,
    extract_area,
    money,
    percentile,
    relevance_score,
)


# ── Тесты _extract_json ────────────────────────────────────────────────────

class TestExtractJson:
    """Парсинг JSON из финального ответа модели — критичная функция оценки."""

    def test_clean_json(self):
        text = '{"auction_price_min": 1000000, "auction_price_max": 1500000, "confidence": "medium"}'
        result = _extract_json(text)
        assert result is not None
        assert result["auction_price_min"] == 1_000_000
        assert result["confidence"] == "medium"

    def test_json_with_surrounding_text(self):
        """Модель часто добавляет текст до и после JSON."""
        text = 'Вот моя оценка:\n{"auction_price_min": 500000, "confidence": "low"}\n\nОбоснование завершено.'
        result = _extract_json(text)
        assert result is not None
        assert result["auction_price_min"] == 500_000

    def test_returns_none_on_no_json(self):
        text = "Модель вернула только текст без JSON"
        result = _extract_json(text)
        assert result is None

    def test_returns_none_on_empty_string(self):
        result = _extract_json("")
        assert result is None

    def test_full_valuation_schema(self):
        """Полная схема ответа модели — все поля присутствуют."""
        data = {
            "quick_lot_min": 300_000,
            "quick_lot_max": 500_000,
            "wholesale_min": 600_000,
            "wholesale_max": 800_000,
            "retail_min": 900_000,
            "retail_max": 1_200_000,
            "auction_price_min": 700_000,
            "auction_price_max": 900_000,
            "confidence": "high",
            "price_per_sqm_min": 50_000,
            "price_per_sqm_max": 70_000,
            "sources": ["avito.ru", "cian.ru"],
            "key_factors": ["хорошее состояние", "центральный район"],
            "reasoning": "Квартира в центре, аналоги найдены на Авито и ЦИАН.",
        }
        result = _extract_json(json.dumps(data))
        assert result is not None
        assert result["auction_price_min"] > 0
        assert result["auction_price_max"] > result["auction_price_min"]
        assert result["retail_min"] > result["auction_price_min"]


# ── Тесты classify_asset ────────────────────────────────────────────────────

class TestClassifyAsset:
    """Классификатор типа актива — определяет стратегию оценки."""

    def test_real_estate_flat(self):
        assert classify_asset("Квартира 2-комнатная, ул. Ленина") == "real_estate"

    def test_real_estate_residential(self):
        assert classify_asset("жилое помещение общей площадью 45 м2") == "real_estate"

    def test_commercial_real_estate(self):
        assert classify_asset("нежилое помещение, офис, этаж 3") == "commercial_real_estate"

    def test_vehicle(self):
        assert classify_asset("Автомобиль Toyota Camry 2019 г., VIN XWEEM81BX10014589") == "vehicle"

    def test_equipment(self):
        assert classify_asset("Станок токарный ТВ-6, оборудование для металлообработки") == "equipment"

    def test_receivable(self):
        assert classify_asset("Дебиторская задолженность ООО «Ромашка» на сумму 5 000 000 руб.") == "receivable"

    def test_shares(self):
        assert classify_asset("Доля 51% в уставном капитале ООО «Капитал»") == "shares_or_business"

    def test_land(self):
        assert classify_asset("Земельный участок категории ИЖС, 15 соток") == "land"

    def test_other(self):
        assert classify_asset("Мебель б/у, стулья 20 шт.") == "other"


# ── Тесты percentile ────────────────────────────────────────────────────────

class TestPercentile:
    """Квантили — основа рыночной оценки по аналогам (P25/P50/P75)."""

    def test_median_odd(self):
        assert percentile([1, 2, 3, 4, 5], 0.5) == pytest.approx(3.0)

    def test_p25(self):
        result = percentile([10_000, 20_000, 30_000, 40_000, 50_000], 0.25)
        assert result == pytest.approx(20_000.0)

    def test_p75(self):
        result = percentile([10_000, 20_000, 30_000, 40_000, 50_000], 0.75)
        assert result == pytest.approx(40_000.0)

    def test_single_value(self):
        assert percentile([100_000], 0.5) == 100_000

    def test_empty_returns_none(self):
        assert percentile([], 0.5) is None

    def test_market_price_calculation(self):
        """Симуляция расчета рыночной цены квартиры через P50."""
        rates_per_m2 = [85_000, 90_000, 95_000, 100_000, 105_000, 110_000, 92_000]
        area = 45.0
        p50 = percentile(rates_per_m2, 0.5)
        market_mid = p50 * area
        assert market_mid is not None
        assert market_mid > 0
        # P50 из [85, 90, 92, 95, 100, 105, 110] * 1000 = 95_000
        assert market_mid == pytest.approx(95_000 * 45.0)


# ── Тесты extract_price ─────────────────────────────────────────────────────

class TestExtractPrice:
    """Извлечение цены из сниппета страницы рыночного аналога."""

    def test_price_with_ruble_sign(self):
        text = "Продаю квартиру за 4 500 000 ₽ торг уместен"
        price = extract_price(text)
        assert price == pytest.approx(4_500_000.0)

    def test_price_with_rub_word(self):
        text = "стоимость 2 300 000 руб."
        price = extract_price(text)
        assert price == pytest.approx(2_300_000.0)

    def test_no_price_returns_none(self):
        text = "Квартира расположена в центре города"
        assert extract_price(text) is None

    def test_price_too_small_ignored(self):
        """Суммы < 100 000 не являются ценами квартир/лотов."""
        text = "аванс 50 000 руб."
        assert extract_price(text) is None


# ── Тесты extract_price_per_m2 ──────────────────────────────────────────────

class TestExtractPricePerM2:
    """Цена за квадратный метр — ключевой параметр сравнения аналогов."""

    def test_rub_per_m2(self):
        text = "цена 95 000 руб. / кв. м"
        price = extract_price_per_m2(text)
        assert price == pytest.approx(95_000.0)

    def test_rub_per_m2_short(self):
        text = "85 000 ₽/м²"
        price = extract_price_per_m2(text)
        assert price == pytest.approx(85_000.0)

    def test_no_price_returns_none(self):
        assert extract_price_per_m2("Хорошая квартира") is None


# ── Тесты extract_area ──────────────────────────────────────────────────────

class TestExtractArea:
    def test_area_from_description(self):
        text = "Квартира общая площадь 67.5 кв. м, 3 комнаты"
        assert extract_area(text) == pytest.approx(67.5)

    def test_area_m2(self):
        text = "45 м2, жилая площадь"
        assert extract_area(text) == pytest.approx(45.0)

    def test_no_area_returns_none(self):
        assert extract_area("Продается лот без описания площади") is None


# ── Тесты clean_description ─────────────────────────────────────────────────

class TestCleanDescription:
    """Очистка описания лота от шаблонного текста перед передачей в LLM."""

    def test_removes_boilerplate(self):
        text = "Квартира 45 м2, хорошее состояние. ВНИМАНИЕ! ВАЖНАЯ информация..."
        result = clean_description(text)
        assert "ВНИМАНИЕ" not in result
        assert "Квартира" in result

    def test_removes_phone(self):
        # Regex в clean_description матчит: +7XXXXXXXXXX (без пробела после +7)
        text = "звоните +79123456789 срочно"
        result = clean_description(text)
        assert "+7" not in result

    def test_removes_phone_with_dash(self):
        text = "тел +7912345-67-89 для связи"
        result = clean_description(text)
        assert "+7" not in result

    def test_empty_returns_empty(self):
        assert clean_description("") == ""

    def test_none_returns_none(self):
        assert clean_description(None) is None


# ── Тесты build_prompt ──────────────────────────────────────────────────────

class TestBuildPrompt:
    """Промпт для LLM строится корректно для разных типов лотов."""

    def test_includes_description(self):
        lot = {"description": "Квартира 45 м2", "start_price": 3_000_000}
        prompt = build_prompt(lot)
        assert "Квартира 45 м2" in prompt

    def test_includes_start_price(self):
        lot = {"description": "Квартира", "start_price": 2_500_000}
        prompt = build_prompt(lot)
        assert "2 500 000" in prompt

    def test_includes_classifier(self):
        lot = {"description": "Оборудование", "classifier": "Станок токарный"}
        prompt = build_prompt(lot)
        assert "Станок токарный" in prompt

    def test_with_documents(self):
        lot = {"description": "Квартира"}
        docs = [{"name": "report.pdf", "text": "Площадь 67 м2, кадастровая стоимость 5 млн"}]
        prompt = build_prompt(lot, documents=docs)
        assert "report.pdf" in prompt
        assert "кадастровая стоимость" in prompt


# ── Тесты money() ────────────────────────────────────────────────────────────

class TestMoney:
    """Парсинг денежных значений из разных форматов API Федресурса."""

    def test_int(self):
        assert money(1_000_000) == pytest.approx(1_000_000.0)

    def test_float(self):
        assert money(1_234_567.89) == pytest.approx(1_234_567.89)

    def test_string_with_spaces(self):
        assert money("1 500 000") == pytest.approx(1_500_000.0)

    def test_string_with_comma(self):
        assert money("2,500,000.50") == pytest.approx(2_500_000.50)

    def test_none_returns_none(self):
        assert money(None) is None

    def test_invalid_string_returns_none(self):
        assert money("нет данных") is None


# ── Тесты format_search_results ─────────────────────────────────────────────

class TestFormatSearchResults:
    def test_formats_results(self):
        results = {
            "results": [
                {"title": "Авито - квартира", "url": "https://avito.ru/123", "content": "Цена 3 млн руб."},
                {"title": "ЦИАН", "url": "https://cian.ru/456", "content": "95 000 руб./м2"},
            ]
        }
        formatted = format_search_results(results)
        assert "Авито" in formatted
        assert "ЦИАН" in formatted
        assert "avito.ru" in formatted

    def test_empty_results(self):
        formatted = format_search_results({"results": []})
        assert "не найдены" in formatted.lower() or formatted == "Результаты не найдены."
