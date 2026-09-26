import { apiClient } from './client';

export type PapelUsuario = 'admin' | 'gestor' | 'corretor';

export interface Membership {
  id: string;
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
}

export interface Convite {
  id: string;
  email: string;
  role: string;
  token: string;
  expires_at: string;
}

export async function listarMemberships(): Promise<Membership[]> {
  const { data } = await apiClient.get<Membership[]>('/auth/memberships');
  return data;
}

export async function convidarUsuario(input: { email: string; role: PapelUsuario }): Promise<Convite> {
  const { data } = await apiClient.post<Convite>('/auth/invitations', input);
  return data;
}

export async function desativarMembership(membershipId: string): Promise<void> {
  await apiClient.post(`/auth/memberships/${membershipId}/deactivate`);
}
