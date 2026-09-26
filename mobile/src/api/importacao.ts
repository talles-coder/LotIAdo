import { Platform } from 'react-native';
import type { DocumentPickerAsset } from 'expo-document-picker';

import { apiClient } from './client';

export type CampoLote = 'identificacao' | 'quadra' | 'area_m2' | 'preco';

export type MapeamentoColunas = Partial<Record<CampoLote, string>>;

export interface ErroLinhaImportacao {
  linha: number;
  erro: string;
}

export interface ResultadoImportacao {
  total_linhas: number;
  importados: number;
  erros: ErroLinhaImportacao[];
}

/**
 * Monta o multipart do CSV. Na web o picker entrega um `File` (`asset.file`); no nativo o React
 * Native aceita o objeto `{ uri, name, type }` como parte do FormData.
 */
function montarFormData(asset: DocumentPickerAsset): FormData {
  const form = new FormData();
  if (Platform.OS === 'web' && asset.file) {
    form.append('arquivo', asset.file, asset.name);
  } else {
    form.append('arquivo', { uri: asset.uri, name: asset.name, type: asset.mimeType ?? 'text/csv' } as unknown as Blob);
  }
  return form;
}

export async function previewImportacaoCsv(loteamentoId: string, asset: DocumentPickerAsset): Promise<string[]> {
  const { data } = await apiClient.post<{ colunas: string[] }>(
    `/loteamentos/${loteamentoId}/lotes/importar/preview`,
    montarFormData(asset),
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return data.colunas;
}

export async function confirmarImportacaoCsv(
  loteamentoId: string,
  asset: DocumentPickerAsset,
  mapeamento: MapeamentoColunas,
): Promise<ResultadoImportacao> {
  const form = montarFormData(asset);
  form.append('mapeamento', JSON.stringify(mapeamento));
  const { data } = await apiClient.post<ResultadoImportacao>(`/loteamentos/${loteamentoId}/lotes/importar`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
