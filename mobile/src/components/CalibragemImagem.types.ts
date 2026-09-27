import type { PontoReferencia } from '../lib/georeferencing';

export interface CalibragemImagemProps {
  imagemUri: string;
  tamanhoImagem: { width: number; height: number } | null;
  onMedirImagem: (tamanho: { width: number; height: number }) => void;
  pontos: PontoReferencia[];
  pontoPendente: [number, number] | null;
  onMarcarPonto: (pixel: [number, number]) => void;
  onConfirmarPonto: (lng: string, lat: string) => void;
}
