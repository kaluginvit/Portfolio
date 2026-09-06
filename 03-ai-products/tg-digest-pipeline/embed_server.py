"""
embed_server.py — персистентный сервер эмбеддингов.

Загружает модель один раз, держит в памяти, отвечает на HTTP-запросы.
Все скрипты обращаются сюда вместо загрузки модели напрямую.

Запуск:
    python embed_server.py

API:
    POST /encode   {"texts": ["...", "..."]}  → {"embeddings": [[...], ...]}
    GET  /health   → {"status": "ok", "model": "...", "dim": 1024}
"""

from __future__ import annotations

import os
import sys
import threading

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import numpy as np
from pathlib import Path

MODEL_NAME = "deepvk/USER-bge-m3"
PORT       = 8767
BATCH_SIZE = 32

print(f"Загружаем модель {MODEL_NAME} …", flush=True)
from sentence_transformers import SentenceTransformer
_model = SentenceTransformer(MODEL_NAME)
_dim   = _model.get_sentence_embedding_dimension()
_lock  = threading.Lock()
print(f"Модель загружена. dim={_dim}. Сервер на порту {PORT}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # тихий лог

    def do_GET(self):
        if self.path == "/health":
            self._json({"status": "ok", "model": MODEL_NAME, "dim": _dim})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path != "/encode":
            self._json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
            texts  = body.get("texts", [])
            if not texts:
                self._json({"embeddings": []})
                return
            with _lock:
                vecs = _model.encode(
                    texts,
                    batch_size=BATCH_SIZE,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                ).astype("float32")
            self._json({"embeddings": vecs.tolist()})
        except Exception as exc:
            self._json({"error": str(exc)}, 500)

    def _json(self, data: dict, code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Готов: http://127.0.0.1:{PORT}/health", flush=True)
    server.serve_forever()
