from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from Haystack.haystack_agent import DEFAULT_KB_NAMESPACE
from logging_setup import setup_logging
from pinecone_manager import PineconeManager

logger = logging.getLogger(__name__)


def _iter_knowledge_files(base_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in ("*.md", "*.txt"):
        files.extend(base_dir.rglob(pattern))
    return sorted(file for file in files if file.is_file())


def _make_chunk_id(relative_path: str, chunk_index: int) -> str:
    digest = hashlib.sha1(f"{relative_path}:{chunk_index}".encode("utf-8")).hexdigest()[:12]
    safe_path = relative_path.replace("\\", "/")
    return f"kb::{safe_path}::{chunk_index}::{digest}"


def _fetch_existing_ids(manager: PineconeManager, ids: list[str], namespace: str) -> set[str]:
    """Return the subset of *ids* that already exist in Pinecone."""
    try:
        result = manager.fetch_vectors(ids, namespace=namespace)
        vectors = getattr(result, "vectors", None) or {}
        if isinstance(vectors, dict):
            return set(vectors.keys())
    except Exception as exc:
        logger.warning("Could not fetch existing vectors for idempotency check: %s", exc)
    return set()


def main() -> None:
    setup_logging()
    load_dotenv()

    knowledge_dir = Path(os.getenv("KNOWLEDGE_BASE_DIR", "knowledge_base")).resolve()
    namespace = os.getenv("PINECONE_KB_NAMESPACE", DEFAULT_KB_NAMESPACE).strip() or DEFAULT_KB_NAMESPACE
    chunk_size = int(os.getenv("KNOWLEDGE_CHUNK_SIZE", "1200"))

    if not knowledge_dir.exists():
        raise FileNotFoundError(
            f"Папка knowledge base не найдена: {knowledge_dir}. "
            "Создай ее и положи туда .md или .txt файлы."
        )

    files = _iter_knowledge_files(knowledge_dir)
    if not files:
        raise ValueError(f"В папке {knowledge_dir} нет .md или .txt файлов для индексации.")

    manager = PineconeManager()

    total_chunks = 0
    total_skipped = 0
    for file_path in files:
        relative_path = file_path.relative_to(knowledge_dir).as_posix()
        text = file_path.read_text(encoding="utf-8")
        chunks = manager.chunk_text(text, chunk_size=chunk_size)

        all_docs: list[dict] = []
        for chunk_index, chunk_text in enumerate(chunks, start=1):
            all_docs.append(
                {
                    "id": _make_chunk_id(relative_path, chunk_index),
                    "text": chunk_text,
                    "metadata": {
                        "doc_type": "knowledge",
                        "source_path": relative_path,
                        "title": file_path.stem,
                        "chunk_index": chunk_index,
                        "chunk_total": len(chunks),
                    },
                }
            )

        # Идемпотентность: пропускаем чанки, которые уже есть в Pinecone.
        all_ids = [doc["id"] for doc in all_docs]
        existing_ids = _fetch_existing_ids(manager, all_ids, namespace)
        new_docs = [doc for doc in all_docs if doc["id"] not in existing_ids]
        skipped = len(all_docs) - len(new_docs)

        if new_docs:
            manager.upsert_documents(new_docs, namespace=namespace)

        total_chunks += len(new_docs)
        total_skipped += skipped
        logger.info(
            "Indexed %s: %d new chunks, %d skipped (already in Pinecone)",
            relative_path, len(new_docs), skipped,
        )

    logger.info(
        "Done. Indexed %d files — %d new chunks, %d skipped, namespace=%r",
        len(files), total_chunks, total_skipped, namespace,
    )


if __name__ == "__main__":
    main()
