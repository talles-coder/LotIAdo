"""Chunking de texto de documentos (decisão D5 — LangChain só para text splitters)."""
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Tamanho/overlap de partida (FASE7-EST-02): grande o suficiente para manter
# contexto de um parágrafo, com overlap para não cortar uma frase relevante
# na fronteira entre dois chunks. Ajustar empiricamente é um refinamento de
# fase futura, não bloqueante para o pipeline funcionar.
TAMANHO_CHUNK = 1000
OVERLAP_CHUNK = 150


def dividir_em_chunks(texto: str) -> list[str]:
    """Divide `texto` em chunks, descartando pedaços vazios (ex.: só espaços)."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=TAMANHO_CHUNK, chunk_overlap=OVERLAP_CHUNK)
    return [chunk for chunk in splitter.split_text(texto) if chunk.strip()]
