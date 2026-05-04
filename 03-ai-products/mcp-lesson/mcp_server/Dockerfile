FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8765
ENV MCP_HOST=0.0.0.0 MCP_PORT=8765
CMD ["python", "server.py", "--http"]
