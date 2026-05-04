FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# stdio MCP для Cursor / Claude Desktop
CMD ["python", "server.py"]
