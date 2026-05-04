FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
VOLUME ["/app/.sync_state"]
# OAuth первый раз — на хосте (см. README), затем монтируйте .sync_state в контейнер.
CMD ["python", "main.py", "sync"]
