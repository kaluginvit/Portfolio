"""
Smoke tests for ФинАналитик API.
Tests cover input validation only — Claude API is NOT called.
Run: pytest backend/tests/ -v
"""
import io
import os

import pytest
from fastapi.testclient import TestClient

# Stub out the API key so imports don't fail in CI without real credentials
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from main import app  # noqa: E402

client = TestClient(app)


def test_health():
    """GET /health should return 200 with status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_invalid_format():
    """POST /upload with unsupported .txt format should return 400."""
    file_content = b"some text content"
    response = client.post(
        "/upload",
        files={"file": ("report.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 400
    assert "txt" in response.json()["detail"].lower()


def test_upload_empty_file():
    """POST /upload with empty file body should return 400."""
    response = client.post(
        "/upload",
        files={"file": ("data.csv", io.BytesIO(b""), "text/csv")},
    )
    assert response.status_code == 400
    assert "пустой" in response.json()["detail"].lower()


def test_chat_no_table_data():
    """POST /chat with empty table_data should return 400."""
    response = client.post(
        "/chat",
        json={"message": "Что в таблице?", "table_data": ""},
    )
    assert response.status_code == 400
    assert "загрузите файл" in response.json()["detail"].lower()


def test_chat_empty_message():
    """POST /chat with blank message should return 400."""
    response = client.post(
        "/chat",
        json={"message": "   ", "table_data": "some data"},
    )
    assert response.status_code == 400
    assert "пустым" in response.json()["detail"].lower()
