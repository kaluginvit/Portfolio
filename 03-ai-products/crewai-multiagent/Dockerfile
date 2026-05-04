FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --prefer-binary -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт для FastAPI
EXPOSE 8001

# Команда по умолчанию - запуск API сервера
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
