import { apiClient } from './client';

export interface Corretor {
  id: string;
  nome: string;
  contato: string;
  usuario_id: string | null;
}

export async function listarCorretores(): Promise<Corretor[]> {
  const { data } = await apiClient.get<Corretor[]>('/corretores');
  return data;
}

export async function obterCorretor(corretorId: string): Promise<Corretor> {
  const { data } = await apiClient.get<Corretor>(`/corretores/${corretorId}`);
  return data;
}

export async function criarCorretor(input: { nome: string; contato: string }): Promise<Corretor> {
  const { data } = await apiClient.post<Corretor>('/corretores', input);
  return data;
}

export async function atualizarCorretor(
  corretorId: string,
  input: { nome: string; contato: string },
): Promise<Corretor> {
  const { data } = await apiClient.patch<Corretor>(`/corretores/${corretorId}`, input);
  return data;
}

export async function removerCorretor(corretorId: string): Promise<void> {
  await apiClient.delete(`/corretores/${corretorId}`);
}
