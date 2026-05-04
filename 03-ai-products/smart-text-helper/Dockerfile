# Интерактивный CLI: `docker run -it --env-file .env ...`
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "test_agent.py"]
