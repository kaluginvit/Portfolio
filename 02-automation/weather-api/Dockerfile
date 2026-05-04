FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# CLI с меню; для неинтерактива передайте команду: docker run -it --env-file .env ...
ENTRYPOINT ["python", "main.py"]
