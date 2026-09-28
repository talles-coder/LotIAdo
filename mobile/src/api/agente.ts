import { apiClient } from './client';

export interface ConfirmacaoAcaoPendente {
  confirmacao_id: string;
  tool: string;
  descricao: string;
  argumentos: Record<string, unknown>;
}

export interface PerguntarAgenteResponse {
  resposta: string | null;
  confirmacao: ConfirmacaoAcaoPendente | null;
}

function normalizar(data: Partial<PerguntarAgenteResponse>): PerguntarAgenteResponse {
  return { resposta: data.resposta ?? null, confirmacao: data.confirmacao ?? null };
}

export async function perguntarAgente(pergunta: string): Promise<PerguntarAgenteResponse> {
  const { data } = await apiClient.post<Partial<PerguntarAgenteResponse>>('/agente/perguntar', { pergunta });
  return normalizar(data);
}

export async function confirmarAcao(confirmacaoId: string, aprovado: boolean): Promise<PerguntarAgenteResponse> {
  const { data } = await apiClient.post<Partial<PerguntarAgenteResponse>>('/agente/confirmar', {
    confirmacao_id: confirmacaoId,
    aprovado,
  });
  return normalizar(data);
}
