"""
Tests for lot_source.py — LotSource abstraction and validation.
No external dependencies, no DB, no API calls.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lot_source import (
    DemoSource,
    LotValidationError,
    SingleLotSource,
    validate_lot,
)


# ─────────────────────────── validate_lot ────────────────────────────────────

class TestValidateLot:
    def test_valid_lot_passes(self):
        lot = {"id": "X-1", "title": "Test lot", "description": "Asset description here"}
        validate_lot(lot)  # should not raise

    def test_missing_id_raises(self):
        with pytest.raises(LotValidationError, match="missing required fields"):
            validate_lot({"title": "T", "description": "desc"})

    def test_missing_title_raises(self):
        with pytest.raises(LotValidationError, match="missing required fields"):
            validate_lot({"id": "X-1", "description": "desc"})

    def test_missing_description_raises(self):
        with pytest.raises(LotValidationError, match="missing required fields"):
            validate_lot({"id": "X-1", "title": "T"})

    def test_description_too_short_raises(self):
        with pytest.raises(LotValidationError, match="too short"):
            validate_lot({"id": "X-1", "title": "T", "description": "short"})

    def test_description_exactly_minimum(self):
        # 10 chars is the minimum
        lot = {"id": "X-1", "title": "T", "description": "1234567890"}
        validate_lot(lot)

    def test_empty_id_raises(self):
        with pytest.raises(LotValidationError):
            validate_lot({"id": "", "title": "T", "description": "description here"})


# ─────────────────────────── DemoSource ──────────────────────────────────────

class TestDemoSource:
    def test_returns_non_empty_list(self):
        lots = DemoSource().get_lots()
        assert len(lots) >= 1

    def test_all_demo_lots_pass_validation(self):
        lots = DemoSource().get_lots()
        for lot in lots:
            validate_lot(lot)  # should not raise

    def test_demo_lots_have_required_fields(self):
        for lot in DemoSource().get_lots():
            assert "id" in lot
            assert "title" in lot
            assert "description" in lot
            assert "start_price" in lot
            assert "asset_type" in lot

    def test_get_valid_lots_returns_all_demo_lots(self):
        source = DemoSource()
        valid = source.get_valid_lots()
        assert len(valid) == len(source.get_lots())

    def test_demo_001_is_real_estate(self):
        lots = {l["id"]: l for l in DemoSource().get_lots()}
        assert lots.get("DEMO-001", {}).get("asset_type") == "real_estate"

    def test_demo_002_is_vehicle(self):
        lots = {l["id"]: l for l in DemoSource().get_lots()}
        assert lots.get("DEMO-002", {}).get("asset_type") == "vehicle"


# ─────────────────────────── get_valid_lots filtering ────────────────────────

class TestGetValidLotsFiltering:
    """LotSource.get_valid_lots() should skip invalid lots without crashing."""

    class _MixedSource(DemoSource):
        """Override to inject an invalid lot."""
        def get_lots(self):
            return [
                {"id": "GOOD-1", "title": "Good lot", "description": "Valid description here"},
                {"id": "",       "title": "Bad lot",  "description": "Has no id"},
                {"id": "GOOD-2", "title": "Good 2",   "description": "Another valid one"},
            ]

    def test_invalid_lot_is_skipped(self, capsys):
        source = self._MixedSource()
        valid = source.get_valid_lots()
        assert len(valid) == 2
        assert all(l["id"] for l in valid)
        # Skipped lot should be logged
        out = capsys.readouterr().out
        assert "[skip]" in out


# ─────────────────────────── SingleLotSource ─────────────────────────────────

class TestSingleLotSource:
    def test_missing_db_raises_lot_validation_error(self, tmp_path):
        source = SingleLotSource("X-1", db_path=tmp_path / "nonexistent.db")
        with pytest.raises(LotValidationError, match="not found"):
            source.get_lots()

    def test_lot_not_in_db_raises(self, tmp_path):
        import sqlite3
        db = tmp_path / "test.db"
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE lots (id TEXT PRIMARY KEY, title TEXT, description TEXT)")
        conn.commit()
        conn.close()

        source = SingleLotSource("MISSING-ID", db_path=db)
        with pytest.raises(LotValidationError, match="not found"):
            source.get_lots()

    def test_lot_found_in_db(self, tmp_path):
        import sqlite3
        db = tmp_path / "test.db"
        conn = sqlite3.connect(db)
        conn.execute(
            "CREATE TABLE lots (id TEXT PRIMARY KEY, title TEXT, description TEXT, status TEXT)"
        )
        conn.execute("INSERT INTO lots VALUES ('LOT-1', 'Test Lot', 'Valid description here', 'active')")
        conn.commit()
        conn.close()

        source = SingleLotSource("LOT-1", db_path=db)
        lots = source.get_lots()
        assert len(lots) == 1
        assert lots[0]["id"] == "LOT-1"
