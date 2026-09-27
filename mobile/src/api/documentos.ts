import { Platform } from 'react-native';
import type { DocumentPickerAsset } from 'expo-document-picker';

import { apiClient } from './client';

export interface IdentificacaoSugerida {
  texto: string;
  confianca: number;
  bbox: [number, number, number, number];
}

export interface ContornoSugerido {
  pontos: [number, number][];
  area: number;
}

/** Sugestão de extração de planta (OCR + contornos, FASE8-IMPL-02/SCRUM-100) — sempre em pixels. */
export interface ResultadoExtracaoImagem {
  identificacoes: IdentificacaoSugerida[];
  contornos: ContornoSugerido[];
}

export interface Documento {
  id: string;
  nome: string;
  tipo: string | null;
  content_type: string;
  tamanho_bytes: number;
  loteamento_id: string | null;
  lote_id: string | null;
  status_extracao_imagem: string | null;
  resultado_extracao_imagem: ResultadoExtracaoImagem | null;
}

export interface FiltroDocumentos {
  loteamentoId?: string;
  loteId?: string;
}

/**
 * Monta o multipart do documento. Na web o picker entrega um `File` (`asset.file`); no nativo o
 * React Native aceita o objeto `{ uri, name, type }` como parte do FormData.
 */
function montarFormData(asset: DocumentPickerAsset): FormData {
  const form = new FormData();
  if (Platform.OS === 'web' && asset.file) {
    form.append('arquivo', asset.file, asset.name);
  } else {
    form.append('arquivo', {
      uri: asset.uri,
      name: asset.name,
      type: asset.mimeType ?? 'application/octet-stream',
    } as unknown as Blob);
  }
  return form;
}

export async function listarDocumentos(filtro: FiltroDocumentos = {}): Promise<Documento[]> {
  const { data } = await apiClient.get<Documento[]>('/documentos', {
    params: { loteamento_id: filtro.loteamentoId, lote_id: filtro.loteId },
  });
  return data;
}

export async function enviarDocumento(
  asset: DocumentPickerAsset,
  opcoes: { tipo?: string; loteamentoId?: string; loteId?: string } = {},
): Promise<Documento> {
  const form = montarFormData(asset);
  if (opcoes.tipo) form.append('tipo', opcoes.tipo);
  if (opcoes.loteamentoId) form.append('loteamento_id', opcoes.loteamentoId);
  if (opcoes.loteId) form.append('lote_id', opcoes.loteId);

  const { data } = await apiClient.post<Documento>('/documentos', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function obterDocumento(documentoId: string): Promise<Documento> {
  const { data } = await apiClient.get<Documento>(`/documentos/${documentoId}`);
  return data;
}

/**
 * Pede a sugestão de extração da planta (OCR + contornos, FASE8-IMPL-02/SCRUM-100): roda
 * assíncrona (job RQ), quem chama faz poll com `obterDocumento` até `status_extracao_imagem`
 * sair de `pendente`/`processando`. Nunca persiste geometria/identificação sozinha.
 */
export async function solicitarExtracaoImagem(documentoId: string): Promise<Documento> {
  const { data } = await apiClient.post<Documento>(`/documentos/${documentoId}/sugerir-extracao-imagem`);
  return data;
}

export async function obterUrlAssinadaDocumento(documentoId: string): Promise<string> {
  const { data } = await apiClient.get<{ url: string }>(`/documentos/${documentoId}/url-assinada`);
  return data.url;
}

export async function removerDocumento(documentoId: string): Promise<void> {
  await apiClient.delete(`/documentos/${documentoId}`);
}
