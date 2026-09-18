import { isAxiosError } from 'axios';

import { apiClient } from './client';
import type { LoteStatus } from './loteamentos';

export type ReservaStatus = 'reservado' | 'vendido' | 'cancelada';
export type ReservaTipo = 'reserva' | 'venda';

export interface Reserva {
  id: string;
  lote_id: string;
  cliente_id: string;
  corretor_id: string | null;
  tipo: ReservaTipo;
  status: ReservaStatus;
}

/** Ações de reserva/venda disponíveis para cada status de lote — espelha a máquina de estados do backend. */
export function acoesDisponiveisParaStatus(status: LoteStatus): {
  reservar: boolean;
  converterVenda: boolean;
  cancelar: boolean;
} {
  return {
    reservar: status === 'disponivel',
    converterVenda: status === 'reservado',
    cancelar: status === 'reservado',
  };
}

export async function obterReservaAtivaPorLote(loteId: string): Promise<Reserva | null> {
  try {
    const { data } = await apiClient.get<Reserva>(`/reservas/ativa-por-lote/${loteId}`);
    return data;
  } catch (err) {
    if (isAxiosError(err) && err.response?.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function criarReserva(input: { loteId: string; clienteId: string }): Promise<Reserva> {
  const { data } = await apiClient.post<Reserva>('/reservas', {
    lote_id: input.loteId,
    cliente_id: input.clienteId,
  });
  return data;
}

export async function converterReservaEmVenda(reservaId: string): Promise<Reserva> {
  const { data } = await apiClient.post<Reserva>(`/reservas/${reservaId}/converter-venda`);
  return data;
}

export async function cancelarReserva(reservaId: string): Promise<Reserva> {
  const { data } = await apiClient.post<Reserva>(`/reservas/${reservaId}/cancelar`);
  return data;
}
