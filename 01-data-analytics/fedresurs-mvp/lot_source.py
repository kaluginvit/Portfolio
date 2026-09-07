"""
lot_source.py — Abstraction for lot input sources.

Separates WHERE lots come from (Chrome bookmarks vs demo seed vs direct ID)
from WHAT valuation does with them.

Usage:
    from lot_source import DemoSource, FedresursDBSource, validate_lot

    source = DemoSource()
    lots = source.get_lots()
    for lot in lots:
        validate_lot(lot)          # raises ValueError if invalid
        print(lot["id"], lot["title"])
"""
from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).parent / "data" / "fedresurs.sqlite3"

# Required fields for a lot to be eligible for valuation
_REQUIRED_LOT_FIELDS = ("id", "title", "description")


# ─────────────────────────── Validation ──────────────────────────────────────

class LotValidationError(ValueError):
    """Raised when a lot does not meet minimum requirements for valuation."""
    pass


def validate_lot(lot: dict[str, Any]) -> None:
    """
    Check that a lot has minimum required fields for valuation.
    Raises LotValidationError with a descriptive message if invalid.
    """
    missing = [f for f in _REQUIRED_LOT_FIELDS if not lot.get(f)]
    if missing:
        lot_id = lot.get("id", "<unknown>")
        raise LotValidationError(
            f"Lot '{lot_id}' is missing required fields: {missing}. "
            "Cannot run valuation without at least id, title, and description."
        )

    # Description must be non-trivially short
    desc = lot.get("description", "")
    if len(desc.strip()) < 10:
        raise LotValidationError(
            f"Lot '{lot['id']}' description too short ({len(desc)} chars). "
            "Valuation requires meaningful asset description."
        )


# ─────────────────────────── Base class ──────────────────────────────────────

class LotSource(ABC):
    """Abstract base: returns a list of lots suitable for valuation."""

    @abstractmethod
    def get_lots(self) -> list[dict[str, Any]]:
        """Return list of lot dicts with at minimum: id, title, description."""
        ...

    def get_valid_lots(self) -> list[dict[str, Any]]:
        """Return only lots that pass validation, logging skipped ones."""
        valid = []
        for lot in self.get_lots():
            try:
                validate_lot(lot)
                valid.append(lot)
            except LotValidationError as e:
                print(f"[skip] {e}")
        return valid


# ─────────────────────────── Implementations ─────────────────────────────────

class FedresursDBSource(LotSource):
    """
    Reads lots from the local SQLite database.
    Lots must already exist (imported via Chrome bookmarks or demo_seed.py).
    """

    def __init__(self, db_path: Path = DB_PATH, status: str | None = "active", limit: int = 50):
        self.db_path = db_path
        self.status = status
        self.limit = limit

    def get_lots(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            return []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            if self.status:
                rows = conn.execute(
                    "SELECT * FROM lots WHERE status = ? ORDER BY id LIMIT ?",
                    (self.status, self.limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM lots ORDER BY id LIMIT ?",
                    (self.limit,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()


class DemoSource(LotSource):
    """
    Returns synthetic lots from demo_seed — does not require Chrome or Fedresurs API.
    Seeds the DB if not already seeded.
    """

    # Synthetic lots mirroring demo_seed.py — no DB dependency for tests
    DEMO_LOTS: list[dict[str, Any]] = [
        {
            "id": "DEMO-001",
            "title": "Квартира 2-комнатная, 54 м², г. Екатеринбург, ул. Малышева",
            "asset_type": "real_estate",
            "start_price": 3_500_000,
            "auction_type": "auction",
            "status": "active",
            "description": (
                "Квартира, общая площадь 54.0 кв.м, жилая 32 кв.м, кухня 9 кв.м. "
                "Этаж 4/9. Кирпичный дом 1986 г."
            ),
        },
        {
            "id": "DEMO-002",
            "title": "Грузовой автомобиль МАЗ-6430, 2015 г.в.",
            "asset_type": "vehicle",
            "start_price": 1_200_000,
            "auction_type": "public_offer",
            "status": "active",
            "description": (
                "Грузовой тягач МАЗ-6430A9-520-031, 2015 г.в., пробег 380 000 км, "
                "двигатель ЯМЗ-651, 412 л.с."
            ),
        },
        {
            "id": "DEMO-003",
            "title": "Производственное оборудование: фрезерный станок ГФ2171",
            "asset_type": "equipment",
            "start_price": 450_000,
            "auction_type": "auction",
            "status": "active",
            "description": (
                "Горизонтально-фрезерный станок ГФ2171, 1989 г.в. "
                "Рабочее состояние, требует технического обслуживания."
            ),
        },
    ]

    def get_lots(self) -> list[dict[str, Any]]:
        return list(self.DEMO_LOTS)


class SingleLotSource(LotSource):
    """
    Source that wraps a single lot by ID from the DB.
    Raises LotValidationError if the lot is not found.
    """

    def __init__(self, lot_id: str, db_path: Path = DB_PATH):
        self.lot_id = lot_id
        self.db_path = db_path

    def get_lots(self) -> list[dict[str, Any]]:
        if not self.db_path.exists():
            raise LotValidationError(f"Database not found: {self.db_path}")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute("SELECT * FROM lots WHERE id = ?", (self.lot_id,)).fetchone()
        finally:
            conn.close()
        if row is None:
            raise LotValidationError(
                f"Lot '{self.lot_id}' not found in database. "
                "Run demo_seed.py to add demo lots, or import real lots first."
            )
        return [dict(row)]
