"""
demo_seed.py — заполняет базу данных синтетическими лотами для демонстрации.

Usage:
    python demo_seed.py

После запуска в data/fedresurs.sqlite3 появятся 5 лотов.
Запустить веб-интерфейс: python server.py
"""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "fedresurs.sqlite3"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DEMO_LOTS = [
    {
        "id": "DEMO-001",
        "title": "Квартира 2-комнатная, 54 м², г. Екатеринбург, ул. Малышева",
        "asset_type": "real_estate",
        "start_price": 3500000,
        "auction_type": "auction",
        "status": "active",
        "description": "Квартира, общая площадь 54.0 кв.м, жилая 32 кв.м, кухня 9 кв.м. Этаж 4/9. Кирпичный дом 1986 г.",
        "source_url": "https://fedresurs.ru/bankruptcy/lot/DEMO-001",
    },
    {
        "id": "DEMO-002",
        "title": "Грузовой автомобиль МАЗ-6430, 2015 г.в.",
        "asset_type": "vehicle",
        "start_price": 1200000,
        "auction_type": "public_offer",
        "status": "active",
        "description": "Грузовой тягач МАЗ-6430A9-520-031, 2015 г.в., пробег 380 000 км, двигатель ЯМЗ-651, 412 л.с.",
        "source_url": "https://fedresurs.ru/bankruptcy/lot/DEMO-002",
    },
    {
        "id": "DEMO-003",
        "title": "Производственное оборудование: фрезерный станок ГФ2171",
        "asset_type": "equipment",
        "start_price": 450000,
        "auction_type": "auction",
        "status": "active",
        "description": "Горизонтально-фрезерный станок ГФ2171, 1989 г.в. Рабочее состояние, требует технического обслуживания.",
        "source_url": "https://fedresurs.ru/bankruptcy/lot/DEMO-003",
    },
    {
        "id": "DEMO-004",
        "title": "Нежилое помещение 120 м², г. Москва, р-н Выхино",
        "asset_type": "real_estate",
        "start_price": 8900000,
        "auction_type": "auction",
        "status": "active",
        "description": "Нежилое помещение на 1 этаже жилого дома, площадь 120 кв.м. Отдельный вход. Подходит под торговлю/офис.",
        "source_url": "https://fedresurs.ru/bankruptcy/lot/DEMO-004",
    },
    {
        "id": "DEMO-005",
        "title": "Дебиторская задолженность ООО «Вектор» — 3 200 000 ₽",
        "asset_type": "receivable",
        "start_price": 320000,
        "auction_type": "public_offer",
        "status": "active",
        "description": "Право требования к ООО «Вектор» (ИНН: XXXXXXXXXX) на сумму 3 200 000 руб. Документально подтверждено, в суде не оспорено.",
        "source_url": "https://fedresurs.ru/bankruptcy/lot/DEMO-005",
    },
]


def seed_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создаём таблицу если не существует
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lots (
            id TEXT PRIMARY KEY,
            title TEXT,
            asset_type TEXT,
            start_price REAL,
            auction_type TEXT,
            status TEXT,
            description TEXT,
            source_url TEXT,
            valuation_json TEXT
        )
    """)

    inserted = 0
    for lot in DEMO_LOTS:
        cursor.execute(
            "INSERT OR IGNORE INTO lots (id, title, asset_type, start_price, auction_type, status, description, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (lot["id"], lot["title"], lot["asset_type"], lot["start_price"],
             lot["auction_type"], lot["status"], lot["description"], lot["source_url"]),
        )
        if cursor.rowcount > 0:
            inserted += 1

    conn.commit()
    conn.close()

    print(f"Demo seed: {inserted} лотов добавлено в {DB_PATH}")
    print("Запустите веб-интерфейс: python server.py")
    print("Или оцените конкретный лот: python valuate.py DEMO-001")


if __name__ == "__main__":
    seed_db()
