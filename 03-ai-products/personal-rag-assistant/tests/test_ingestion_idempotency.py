"""
Тест идемпотентности: повторный запуск ingest_knowledge_base не дублирует записи в Pinecone.

Pinecone полностью замокирован — внешние вызовы не выполняются.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers — дублируем логику ID из ingest_knowledge_base, чтобы не импортировать
# модуль с транзитивными зависимостями (Haystack, Pinecone) напрямую.
# ---------------------------------------------------------------------------

def _make_chunk_id(relative_path: str, chunk_index: int) -> str:
    digest = hashlib.sha1(f"{relative_path}:{chunk_index}".encode("utf-8")).hexdigest()[:12]
    safe_path = relative_path.replace("\\", "/")
    return f"kb::{safe_path}::{chunk_index}::{digest}"


def _make_fake_fetch_result(existing_ids: set[str]) -> Any:
    """Simulate a Pinecone fetch response that contains `existing_ids`."""
    mock = MagicMock()
    mock.vectors = {vid: MagicMock() for vid in existing_ids}
    return mock


# ---------------------------------------------------------------------------
# Unit-тесты
# ---------------------------------------------------------------------------

class TestMakeChunkId:
    def test_deterministic(self) -> None:
        id1 = _make_chunk_id("docs/file.md", 1)
        id2 = _make_chunk_id("docs/file.md", 1)
        assert id1 == id2

    def test_different_chunk_gives_different_id(self) -> None:
        assert _make_chunk_id("docs/file.md", 1) != _make_chunk_id("docs/file.md", 2)

    def test_different_path_gives_different_id(self) -> None:
        assert _make_chunk_id("docs/a.md", 1) != _make_chunk_id("docs/b.md", 1)

    def test_starts_with_kb_prefix(self) -> None:
        assert _make_chunk_id("readme.md", 1).startswith("kb::")


class TestFetchExistingIds:
    """Проверяет логику фильтрации уже существующих чанков."""

    def test_returns_only_existing_ids(self) -> None:
        from ingest_knowledge_base import _fetch_existing_ids

        manager = MagicMock()
        chunk_id_1 = _make_chunk_id("doc.md", 1)
        chunk_id_2 = _make_chunk_id("doc.md", 2)
        manager.fetch_vectors.return_value = _make_fake_fetch_result({chunk_id_1})

        result = _fetch_existing_ids(manager, [chunk_id_1, chunk_id_2], namespace="test-ns")

        assert chunk_id_1 in result
        assert chunk_id_2 not in result

    def test_returns_empty_set_on_exception(self) -> None:
        from ingest_knowledge_base import _fetch_existing_ids

        manager = MagicMock()
        manager.fetch_vectors.side_effect = RuntimeError("Pinecone unavailable")

        result = _fetch_existing_ids(manager, [_make_chunk_id("doc.md", 1)], namespace="ns")

        assert result == set()


class TestIngestionIdempotency:
    """Интеграционный тест: двойной запуск main() не дублирует upsert для уже загруженных ID."""

    def test_second_run_skips_existing_chunks(self, tmp_path: Path) -> None:
        # Создаём тестовый файл знаний
        kb_dir = tmp_path / "knowledge_base"
        kb_dir.mkdir()
        (kb_dir / "test_doc.md").write_text("Это тестовый документ для проверки идемпотентности.", encoding="utf-8")

        # Вычисляем ожидаемый ID первого чанка
        expected_id = _make_chunk_id("test_doc.md", 1)

        mock_manager = MagicMock()
        # Первый вызов fetch — файл ещё не загружен
        mock_manager.fetch_vectors.return_value = _make_fake_fetch_result(set())
        mock_manager.chunk_text.return_value = ["Это тестовый документ для проверки идемпотентности."]

        with (
            patch("ingest_knowledge_base.PineconeManager", return_value=mock_manager),
            patch.dict("os.environ", {"KNOWLEDGE_BASE_DIR": str(kb_dir), "PINECONE_KB_NAMESPACE": "kb"}),
        ):
            from ingest_knowledge_base import main
            main()

        # Первый запуск — upsert должен быть вызван
        assert mock_manager.upsert_documents.call_count == 1
        first_call_docs = mock_manager.upsert_documents.call_args_list[0][0][0]
        assert any(doc["id"] == expected_id for doc in first_call_docs)

        # Второй запуск — Pinecone "знает" об этом ID
        mock_manager.reset_mock()
        mock_manager.chunk_text.return_value = ["Это тестовый документ для проверки идемпотентности."]
        mock_manager.fetch_vectors.return_value = _make_fake_fetch_result({expected_id})

        with (
            patch("ingest_knowledge_base.PineconeManager", return_value=mock_manager),
            patch.dict("os.environ", {"KNOWLEDGE_BASE_DIR": str(kb_dir), "PINECONE_KB_NAMESPACE": "kb"}),
        ):
            main()

        # Второй запуск — upsert не вызывался (все чанки уже существуют)
        mock_manager.upsert_documents.assert_not_called()

    def test_partial_reupload_only_new_chunks(self, tmp_path: Path) -> None:
        """Если часть чанков уже есть — загружаются только новые."""
        kb_dir = tmp_path / "knowledge_base"
        kb_dir.mkdir()
        (kb_dir / "big_doc.md").write_text("chunk one | chunk two", encoding="utf-8")

        id_chunk_1 = _make_chunk_id("big_doc.md", 1)
        id_chunk_2 = _make_chunk_id("big_doc.md", 2)

        mock_manager = MagicMock()
        mock_manager.chunk_text.return_value = ["chunk one", "chunk two"]
        # Chunk 1 уже существует, chunk 2 — нет
        mock_manager.fetch_vectors.return_value = _make_fake_fetch_result({id_chunk_1})

        with (
            patch("ingest_knowledge_base.PineconeManager", return_value=mock_manager),
            patch.dict("os.environ", {"KNOWLEDGE_BASE_DIR": str(kb_dir), "PINECONE_KB_NAMESPACE": "kb"}),
        ):
            from ingest_knowledge_base import main
            main()

        assert mock_manager.upsert_documents.call_count == 1
        uploaded_ids = [doc["id"] for doc in mock_manager.upsert_documents.call_args_list[0][0][0]]
        assert id_chunk_1 not in uploaded_ids
        assert id_chunk_2 in uploaded_ids
