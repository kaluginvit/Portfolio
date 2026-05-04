FROM python:3.11-slim-bookworm

# Интеграция Pinecone ↔ Haystack: пакет pinecone-haystack (не haystack-integrations).

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# На slim часть транзитивных зависимостей может собираться из исходников без wheel → нужен gcc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
