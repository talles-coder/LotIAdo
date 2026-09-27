"""OCR (Tesseract) + detecção de contornos (OpenCV) para sugestão de extração de plantas.

Pipeline puro (sem I/O de banco/fila) usado pelo job em
`app/documentos/application/extracao_imagem_service.py` (FASE8-IMPL-02/SCRUM-100): extrai texto
candidato a identificação de lote (OCR) e contornos aproximados de polígono, ambos em coordenadas
de pixel da imagem — nunca geográficas. Nenhuma técnica aqui produz coordenada real sozinha; a
conversão via calibração manual e a persistência ficam por conta da tela de revisão (FASE5-IMPL-03).
"""
import cv2
import numpy as np
import pytesseract

# Confiança 0-100 que o Tesseract atribui a cada palavra; abaixo disso é ruído (texto de
# construção, sujeira do scan), não uma identificação candidata.
CONFIANCA_MINIMA_OCR = 40.0
# Área mínima (px²) para um contorno ser um candidato a lote, não ruído de traço/texto.
AREA_MINIMA_CONTORNO = 500.0
# Teto de contornos sugeridos por planta, para a tela de revisão não virar uma lista ilegível.
MAX_CONTORNOS = 30


def _decodificar_imagem(imagem_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(imagem_bytes, dtype=np.uint8)
    imagem = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if imagem is None:
        raise ValueError("Não foi possível decodificar a imagem da planta")
    return imagem


def _ocr_dados(imagem: np.ndarray) -> dict:
    # Tenta com o pacote de idioma "por" (identificações costumam vir em português); cai para o
    # padrão do Tesseract se o pacote não estiver instalado no ambiente (ver infra/worker/Dockerfile).
    try:
        return pytesseract.image_to_data(imagem, lang="por", output_type=pytesseract.Output.DICT)
    except pytesseract.TesseractError:
        return pytesseract.image_to_data(imagem, output_type=pytesseract.Output.DICT)


def extrair_identificacoes(imagem_bytes: bytes) -> list[dict]:
    """OCR sobre a imagem: textos candidatos a identificação de lote, com posição e confiança."""
    dados = _ocr_dados(_decodificar_imagem(imagem_bytes))

    identificacoes = []
    for i, texto_bruto in enumerate(dados["text"]):
        texto = texto_bruto.strip()
        confianca = float(dados["conf"][i])
        if not texto or confianca < CONFIANCA_MINIMA_OCR:
            continue
        identificacoes.append(
            {
                "texto": texto,
                "confianca": confianca,
                "bbox": [dados["left"][i], dados["top"][i], dados["width"][i], dados["height"][i]],
            }
        )
    return identificacoes


def extrair_contornos(imagem_bytes: bytes) -> list[dict]:
    """Detecção de contornos: polígonos aproximados (em pixel) dos maiores contornos da imagem."""
    imagem = _decodificar_imagem(imagem_bytes)
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    _, binaria = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contornos, _ = cv2.findContours(binaria, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    candidatos = []
    for contorno in contornos:
        area = cv2.contourArea(contorno)
        if area < AREA_MINIMA_CONTORNO:
            continue
        perimetro = cv2.arcLength(contorno, True)
        aproximado = cv2.approxPolyDP(contorno, 0.01 * perimetro, True)
        if len(aproximado) < 3:
            continue
        candidatos.append(
            {
                "pontos": [[int(ponto[0][0]), int(ponto[0][1])] for ponto in aproximado],
                "area": float(area),
            }
        )

    candidatos.sort(key=lambda candidato: candidato["area"], reverse=True)
    return candidatos[:MAX_CONTORNOS]


def extrair_sugestoes(imagem_bytes: bytes) -> dict:
    """Roda OCR + detecção de contornos; resultado é só sugestão, nunca persistida sozinha."""
    return {
        "identificacoes": extrair_identificacoes(imagem_bytes),
        "contornos": extrair_contornos(imagem_bytes),
    }
