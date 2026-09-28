import { apiClient } from './client';

export interface MetricasPorOrigem {
  origem: string;
  total_chamadas: number;
  chamadas_com_erro: number;
  latencia_media_ms: number | null;
}

export interface MetricasIA {
  total_chamadas: number;
  chamadas_com_erro: number;
  taxa_erro: number;
  latencia_media_ms: number | null;
  por_origem: MetricasPorOrigem[];
}

export async function obterMetricasIA(): Promise<MetricasIA> {
  const { data } = await apiClient.get<MetricasIA>('/observabilidade/metricas');
  return data;
}
