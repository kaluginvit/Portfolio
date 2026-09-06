"""
Tests for pure utility functions in fetch_bankrot_trades.py.
No network access — all functions tested with synthetic data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fetch_bankrot_trades import (
    _match_lot_field,
    _match_lot_field_api,
    _normalize_lot,
    _looks_like_real_lot,
    _slim_str,
    _message_id_from_url,
    _lot_dedup_key,
    slim_rows_from_card,
)


# ── _slim_str ──────────────────────────────────────────────────────────────────

class TestSlimStr:
    def test_none_returns_empty(self):
        assert _slim_str(None) == ""

    def test_string_stripped(self):
        assert _slim_str("  hello  ") == "hello"

    def test_number(self):
        assert _slim_str(42) == "42"

    def test_dict_serialized(self):
        result = _slim_str({"key": "val"})
        assert "key" in result

    def test_null_bytes_removed(self):
        assert "\x00" not in _slim_str("abc\x00def")


# ── _message_id_from_url ───────────────────────────────────────────────────────

class TestMessageIdFromUrl:
    def test_messagewindow_id(self):
        url = "https://old.bankrot.fedresurs.ru/MessageWindow.aspx?ID=ABCDEF1234567890ABCDEF1234567890"
        assert _message_id_from_url(url) == "ABCDEF1234567890ABCDEF1234567890"

    def test_bankruptmessages_guid(self):
        url = "https://fedresurs.ru/bankruptmessages/ABCDEF1234567890ABCDEF1234567890"
        assert _message_id_from_url(url) == "ABCDEF1234567890ABCDEF1234567890"

    def test_invalid_url_returns_none(self):
        assert _message_id_from_url("https://example.com/page") is None

    def test_empty_string_returns_none(self):
        assert _message_id_from_url("") is None


# ── _match_lot_field ───────────────────────────────────────────────────────────

class TestMatchLotField:
    def test_lot_number_variants(self):
        assert _match_lot_field("Номер лота", "Лот №")
        assert _match_lot_field("Номер лота", "номер лота")
        assert _match_lot_field("Номер лота", "лот")

    def test_description_variants(self):
        assert _match_lot_field("Описание", "Описание имущества")
        assert _match_lot_field("Описание", "предмет торгов")

    def test_price_variants(self):
        assert _match_lot_field("Начальная цена, руб.", "Начальная цена")
        assert _match_lot_field("Начальная цена, руб.", "Стартовая цена, руб.")
        assert _match_lot_field("Начальная цена, руб.", "цена, руб.")

    def test_step(self):
        assert _match_lot_field("Шаг", "шаг")
        assert _match_lot_field("Шаг", "шаг аукциона")

    def test_deposit(self):
        assert _match_lot_field("Задаток", "задаток")
        assert _match_lot_field("Задаток", "размер задатка")

    def test_no_match(self):
        assert not _match_lot_field("Номер лота", "дата публикации")
        assert not _match_lot_field("Описание", "организатор")


# ── _match_lot_field_api ───────────────────────────────────────────────────────

class TestMatchLotFieldApi:
    def test_english_keys(self):
        assert _match_lot_field_api("Номер лота", "lotNumber")
        assert _match_lot_field_api("Описание", "description")
        assert _match_lot_field_api("Начальная цена, руб.", "startPrice")
        assert _match_lot_field_api("Шаг", "step")
        assert _match_lot_field_api("Задаток", "deposit")


# ── _normalize_lot ─────────────────────────────────────────────────────────────

class TestNormalizeLot:
    def test_canonical_fields_extracted(self):
        raw = {
            "Лот №": "1",
            "Описание имущества": "Квартира 45 кв.м.",
            "Начальная цена, руб.": "3 500 000",
            "шаг": "350 000",
            "задаток": "350 000",
        }
        norm = _normalize_lot(raw)
        assert norm.get("Номер лота") == "1"
        assert "Квартира" in norm.get("Описание", "")
        assert "3 500 000" in norm.get("Начальная цена, руб.", "")

    def test_empty_input_returns_empty(self):
        assert _normalize_lot({}) == {}

    def test_irrelevant_keys_excluded(self):
        raw = {"дата публикации": "01.01.2024", "организатор": "ООО Торги"}
        norm = _normalize_lot(raw)
        assert norm == {}


# ── _looks_like_real_lot ──────────────────────────────────────────────────────

class TestLooksLikeRealLot:
    def test_real_lot_with_long_description(self):
        lot = {"Описание": "Квартира двухкомнатная общей площадью 45 кв.м., расположенная по адресу"}
        assert _looks_like_real_lot(lot)

    def test_real_lot_with_price(self):
        lot = {"Начальная цена, руб.": "3 500 000", "Описание": "Помещение"}
        assert _looks_like_real_lot(lot)

    def test_junk_lot_rejected(self):
        lot = {"Описание": ""}
        assert not _looks_like_real_lot(lot)

    def test_empty_lot_rejected(self):
        assert not _looks_like_real_lot({})


# ── _lot_dedup_key ────────────────────────────────────────────────────────────

class TestLotDedupKey:
    def test_same_lot_same_key(self):
        lot = {
            "Номер лота": "1",
            "Начальная цена, руб.": "1000000",
            "Описание": "Земельный участок",
        }
        assert _lot_dedup_key(lot) == _lot_dedup_key(lot)

    def test_different_lots_different_keys(self):
        lot1 = {"Номер лота": "1", "Начальная цена, руб.": "1000000", "Описание": "Участок А"}
        lot2 = {"Номер лота": "2", "Начальная цена, руб.": "2000000", "Описание": "Участок Б"}
        assert _lot_dedup_key(lot1) != _lot_dedup_key(lot2)


# ── slim_rows_from_card ───────────────────────────────────────────────────────

class TestSlimRowsFromCard:
    def test_card_with_lots_produces_one_row_per_lot(self):
        card = {
            "url": "https://fedresurs.ru/bankruptmessages/ABCDEF1234567890ABCDEF1234567890",
            "id": "ABCDEF1234567890ABCDEF1234567890",
            "fields": {"Должник": "ООО Пример", "ИНН": "1234567890"},
            "lots": [
                {"Описание": "Квартира 45 кв.м.", "Начальная цена, руб.": "3 500 000"},
                {"Описание": "Автомобиль BMW", "Начальная цена, руб.": "1 200 000"},
            ],
        }
        rows = slim_rows_from_card(card)
        assert len(rows) == 2
        assert all("url" in r for r in rows)

    def test_card_without_lots_produces_one_row(self):
        card = {
            "url": "https://example.com",
            "id": "test",
            "fields": {"Должник": "ИП Иванов"},
            "lots": [],
        }
        rows = slim_rows_from_card(card)
        assert len(rows) == 1

    def test_url_preserved_in_rows(self):
        url = "https://fedresurs.ru/bankruptmessages/ABCDEF1234567890ABCDEF1234567890"
        card = {"url": url, "id": "test", "fields": {}, "lots": []}
        rows = slim_rows_from_card(card)
        assert rows[0]["url"] == url

    def test_idempotent_call(self):
        """Повторный вызов с теми же данными даёт тот же результат."""
        card = {
            "url": "https://example.com",
            "id": "abc",
            "fields": {"ИНН": "1234567890"},
            "lots": [{"Описание": "Объект недвижимости площадью 100 кв.м.", "Начальная цена, руб.": "5000000"}],
        }
        rows1 = slim_rows_from_card(card)
        rows2 = slim_rows_from_card(card)
        assert rows1 == rows2
