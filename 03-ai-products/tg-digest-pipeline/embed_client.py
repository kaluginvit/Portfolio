"""
embed_client.py — клиент для embed_server.py.

Если сервер недоступен — грузит модель локально как fallback.
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
import numpy as np

EMBED_SERVER_URL = os.environ.get("EMBED_SERVER_URL", "http://127.0.0.1:8767")
_local_model = None


def _try_server(texts: list[str]) -> np.ndarray | None:
    try:
        body = json.dumps({"texts": texts}, ensure_ascii=False).encode("utf-8")
        req  = urllib.request.Request(
            f"{EMBED_SERVER_URL}/encode",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
        return np.array(data["embeddings"], dtype="float32")
    except Exception:
        return None


def _local_encode(texts: list[str]) -> np.ndarray:
    global _local_model
    import os as _os
    _os.environ.setdefault("OMP_NUM_THREADS", "1")
    _os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    if _local_model is None:
        from sentence_transformers import SentenceTransformer
        print("embed_server недоступен — загружаем модель локально…", flush=True)
        _local_model = SentenceTransformer("deepvk/USER-bge-m3")
    return _local_model.encode(
        texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False
    ).astype("float32")


def encode(texts: list[str]) -> np.ndarray:
    """Кодирует тексты. Сначала пробует embed_server, затем локальная модель."""
    if not texts:
        return np.empty((0, 1024), dtype="float32")
    vecs = _try_server(texts)
    if vecs is not None:
        return vecs
    return _local_encode(texts)


def is_server_up() -> bool:
    try:
        urllib.request.urlopen(f"{EMBED_SERVER_URL}/health", timeout=2)
        return True
    except Exception:
        return False
