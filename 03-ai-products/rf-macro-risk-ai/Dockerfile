FROM python:3.12-slim
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev
COPY src/ ./src/
COPY criteria.json criteria_small.json ./
COPY archive/ ./archive/
ENTRYPOINT ["uv", "run", "python", "src/lc_money_alert_bot.py"]
