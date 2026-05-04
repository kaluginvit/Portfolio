# Chromium для Playwright/Scrapling (этап карточек).
FROM python:3.12-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium
COPY . .
ENTRYPOINT ["python", "fetch_bankrot_trades.py"]
CMD ["--help"]
