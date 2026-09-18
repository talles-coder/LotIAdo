import { apiClient } from './client';

export interface Cliente {
  id: string;
  nome: string;
  documento: string;
  contato: string;
}

export async function listarClientes(): Promise<Cliente[]> {
  const { data } = await apiClient.get<Cliente[]>('/clientes');
  return data;
}

export async function criarCliente(input: {
  nome: string;
  documento: string;
  contato: string;
}): Promise<Cliente> {
  const { data } = await apiClient.post<Cliente>('/clientes', input);
  return data;
}
