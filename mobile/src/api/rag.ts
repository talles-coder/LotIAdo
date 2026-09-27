import { apiClient } from './client';

export interface FonteResposta {
  documento_id: string;
  documento_nome: string;
  trecho: string;
}

export interface PerguntaPayload {
  pergunta: string;
  loteamentoId?: string;
  loteId?: string;
}

export interface PerguntaResponse {
  resposta: string;
  fontes: FonteResposta[];
}

export async function perguntar(payload: PerguntaPayload): Promise<PerguntaResponse> {
  const { data } = await apiClient.post<PerguntaResponse>('/rag/perguntar', {
    pergunta: payload.pergunta,
    loteamento_id: payload.loteamentoId ?? null,
    lote_id: payload.loteId ?? null,
  });
  return data;
}
