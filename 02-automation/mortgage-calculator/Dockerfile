FROM python:3.12-slim
WORKDIR /app
ENV FLASK_RUN_HOST=0.0.0.0 FLASK_RUN_PORT=5000
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
