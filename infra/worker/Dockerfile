FROM python:3.11-slim

WORKDIR /app

# tesseract-ocr (+ pacote pt) e libs de runtime do OpenCV (FASE8-IMPL-02/SCRUM-100): o job de
# extração de imagem roda só aqui no worker, nunca inline na API.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Contexto de build é a raiz do repo (ver docker-compose.yml), porque o
# worker roda o mesmo código do backend (app/ai_rag, app/documentos, etc.),
# que hoje só existe em backend/app — sem duplicar em infra/worker.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

CMD ["python", "-m", "app.worker"]
