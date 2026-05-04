# Полный bookworm (не slim): меньше сюрпризов с колёсами и системными либами при pip на Linux CI.
FROM python:3.11-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120

# gcc на случай сборки из исходников; libgomp — часто нужен numpy/onnx-транзитивам.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --prefer-binary -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
