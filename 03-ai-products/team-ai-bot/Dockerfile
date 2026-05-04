FROM python:3.11-slim-bookworm

# Интеграция Pinecone ↔ Haystack: пакет pinecone-haystack (не haystack-integrations).

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
