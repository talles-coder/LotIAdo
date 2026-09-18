import { apiClient } from './client';

export type LoteStatus = 'disponivel' | 'reservado' | 'vendido' | 'indisponivel';

export interface Loteamento {
  id: string;
  nome: string;
  descricao: string | null;
}

export interface Lote {
  id: string;
  loteamento_id: string;
  identificacao: string;
  quadra: string | null;
  area_m2: string | null;
  preco: string | null;
  status: LoteStatus;
  caracteristicas: Record<string, unknown> | null;
  corretor_id: string | null;
  cliente_id: string | null;
}

export async function listarLoteamentos(): Promise<Loteamento[]> {
  const { data } = await apiClient.get<Loteamento[]>('/loteamentos');
  return data;
}

export async function obterLoteamento(loteamentoId: string): Promise<Loteamento> {
  const { data } = await apiClient.get<Loteamento>(`/loteamentos/${loteamentoId}`);
  return data;
}

export async function listarLotes(loteamentoId: string): Promise<Lote[]> {
  const { data } = await apiClient.get<Lote[]>(`/loteamentos/${loteamentoId}/lotes`);
  return data;
}

export async function obterLote(loteId: string): Promise<Lote> {
  const { data } = await apiClient.get<Lote>(`/lotes/${loteId}`);
  return data;
}
