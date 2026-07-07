FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -m src.rag.build_index

CMD ["uvicorn", "src.mcp_server.server:app", "--host", "0.0.0.0", "--port", "8080"]