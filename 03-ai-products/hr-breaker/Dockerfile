FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libgobject-2.0-0 \
    libcairo2 libffi-dev fonts-liberation && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev
COPY src/ ./src/
COPY templates/ ./templates/
EXPOSE 8899
CMD ["uv", "run", "hr-breaker", "serve", "--host", "0.0.0.0", "--port", "8899"]
