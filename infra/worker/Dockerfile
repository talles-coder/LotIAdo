FROM python:3.11-slim

WORKDIR /app

# Contexto de build é a raiz do repo (ver docker-compose.yml), porque o
# worker roda o mesmo código do backend (app/ai_rag, app/documentos, etc.),
# que hoje só existe em backend/app — sem duplicar em infra/worker.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

CMD ["python", "-m", "app.worker"]
