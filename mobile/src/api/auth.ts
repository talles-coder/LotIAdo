import { apiClient } from './client';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<string> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login', { email, password });
  return data.access_token;
}

export interface UsuarioAtual {
  id: string;
  email: string;
  full_name: string | null;
  tenant_id: string | null;
}

export async function obterUsuarioAtual(): Promise<UsuarioAtual> {
  const { data } = await apiClient.get<UsuarioAtual>('/auth/me');
  return data;
}
