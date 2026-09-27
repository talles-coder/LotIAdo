import type { ResultadoExtracaoImagem } from '../api/documentos';
import type { PontoReferencia } from '../lib/georeferencing';

export interface CalibragemImagemProps {
  imagemUri: string;
  tamanhoImagem: { width: number; height: number } | null;
  onMedirImagem: (tamanho: { width: number; height: number }) => void;
  pontos: PontoReferencia[];
  pontoPendente: [number, number] | null;
  onMarcarPonto: (pixel: [number, number]) => void;
  onConfirmarPonto: (lng: string, lat: string) => void;
  /** Sugestão de extração de planta (FASE8-IMPL-02/SCRUM-100), exibida como camada opcional. */
  sugestao?: ResultadoExtracaoImagem | null;
  sugestaoCarregando?: boolean;
  contornoSelecionado?: number | null;
  onSelecionarContorno?: (indice: number | null) => void;
}
