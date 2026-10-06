import { useState } from 'react';
import { Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as DocumentPicker from 'expo-document-picker';
import { ActivityIndicator, Button, HelperText } from 'react-native-paper';
import { ArrowLeft, MapPin } from 'lucide-react-native';

import { enviarDocumento, obterDocumento, solicitarExtracaoImagem } from '../../../src/api/documentos';
import { atualizarGeometriaLote, obterLote, type GeoJsonPolygon } from '../../../src/api/loteamentos';
import { getErrorMessage } from '../../../src/lib/errors';
import { calibrarTransformacao, type PontoReferencia } from '../../../src/lib/georeferencing';
import { colors, fonts } from '../../../src/theme/tokens';
import { shared } from '../../../src/theme/shared';
import { CalibragemImagem } from '../../../src/components/CalibragemImagem';
import { PoligonoEditorMapa, type ImagemOverlay } from '../../../src/components/PoligonoEditorMapa';

const STATUS_EXTRACAO_EM_ANDAMENTO = new Set(['pendente', 'processando']);

/** Passo auxiliar de calibração: marcar 2–3 pontos de referência conhecidos de uma planta não
 * georreferenciada antes de posicionar o desenho sobre o mapa real (docs/01-analise-requisitos.md, seção 8).
 *
 * Também dispara a sugestão de extração da IA (FASE8-IMPL-02/SCRUM-100): ao escolher a imagem, ela é
 * enviada como documento e o backend roda OCR + detecção de contornos em segundo plano (fila RQ). O
 * resultado só preenche a camada de sugestão do `CalibragemImagem` — nada é aplicado automaticamente.
 */
function useCalibragem(loteId: string) {
  const [imagemUri, setImagemUri] = useState<string | null>(null);
  const [tamanhoImagem, setTamanhoImagem] = useState<{ width: number; height: number } | null>(null);
  const [pontos, setPontos] = useState<PontoReferencia[]>([]);
  const [pontoPendente, setPontoPendente] = useState<[number, number] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [documentoId, setDocumentoId] = useState<string | null>(null);
  const [contornoSelecionado, setContornoSelecionado] = useState<number | null>(null);

  const sugestaoMutation = useMutation({
    mutationFn: async (asset: DocumentPicker.DocumentPickerAsset) => {
      const documento = await enviarDocumento(asset, { tipo: 'planta', loteId });
      await solicitarExtracaoImagem(documento.id);
      return documento.id;
    },
    onSuccess: setDocumentoId,
    // Falha ao pedir a sugestão (ex.: rede) não bloqueia a calibração manual — só não há camada de IA.
  });

  const documentoQuery = useQuery({
    queryKey: ['documentos', documentoId, 'extracao-imagem'],
    queryFn: () => obterDocumento(documentoId as string),
    enabled: documentoId !== null,
    refetchInterval: (query) =>
      STATUS_EXTRACAO_EM_ANDAMENTO.has(query.state.data?.status_extracao_imagem ?? '') ? 1500 : false,
  });

  function escolherImagem(asset: DocumentPicker.DocumentPickerAsset) {
    setImagemUri(asset.uri);
    setTamanhoImagem(null);
    setDocumentoId(null);
    setContornoSelecionado(null);
    sugestaoMutation.mutate(asset);
  }

  function adicionarPonto(lng: string, lat: string) {
    if (!pontoPendente) return;
    const lngNum = Number(lng.replace(',', '.'));
    const latNum = Number(lat.replace(',', '.'));
    if (Number.isNaN(lngNum) || Number.isNaN(latNum)) {
      setErro('Informe longitude e latitude válidas.');
      return;
    }
    setPontos((atual) => [...atual, { pixel: pontoPendente, lngLat: [lngNum, latNum] }]);
    setPontoPendente(null);
    setErro(null);
  }

  function calibrar(): ImagemOverlay | null {
    if (!imagemUri || !tamanhoImagem || pontos.length < 2) return null;
    try {
      const transformacao = calibrarTransformacao(pontos);
      const { width, height } = tamanhoImagem;
      const cantos: ImagemOverlay['cantos'] = [
        transformacao.aplicar([0, 0]),
        transformacao.aplicar([width, 0]),
        transformacao.aplicar([width, height]),
        transformacao.aplicar([0, height]),
      ];
      return { url: imagemUri, cantos };
    } catch (err) {
      setErro(getErrorMessage(err, 'Não foi possível calibrar a planta com esses pontos.'));
      return null;
    }
  }

  /** Converte o contorno sugerido escolhido (pixel) em geometria real, via a mesma calibração —
   * é isso que faz "editar uma sugestão" ser mais rápido que desenhar o polígono do zero. */
  function obterPoligonoSugerido(): GeoJsonPolygon | null {
    const contorno =
      contornoSelecionado !== null
        ? documentoQuery.data?.resultado_extracao_imagem?.contornos[contornoSelecionado]
        : undefined;
    if (!contorno || pontos.length < 2) return null;
    try {
      const transformacao = calibrarTransformacao(pontos);
      const anel = contorno.pontos.map((pixel) => transformacao.aplicar(pixel));
      anel.push(anel[0]);
      return { type: 'Polygon', coordinates: [anel] };
    } catch {
      return null;
    }
  }

  const statusExtracao = documentoQuery.data?.status_extracao_imagem ?? null;

  return {
    imagemUri,
    escolherImagem,
    tamanhoImagem,
    setTamanhoImagem,
    pontos,
    pontoPendente,
    setPontoPendente,
    adicionarPonto,
    erro,
    calibrar,
    obterPoligonoSugerido,
    sugestao: documentoQuery.data?.resultado_extracao_imagem ?? null,
    sugestaoCarregando: sugestaoMutation.isPending || STATUS_EXTRACAO_EM_ANDAMENTO.has(statusExtracao ?? ''),
    contornoSelecionado,
    setContornoSelecionado,
  };
}

export default function GeometriaDoLoteScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [modo, setModo] = useState<'editar' | 'calibrar'>('editar');
  const [imagemOverlay, setImagemOverlay] = useState<ImagemOverlay | null>(null);
  const [poligonoSugerido, setPoligonoSugerido] = useState<GeoJsonPolygon | null>(null);
  const [geometria, setGeometria] = useState<GeoJsonPolygon | null>(null);
  const [erroSalvar, setErroSalvar] = useState<string | null>(null);
  const calibragem = useCalibragem(id);

  const loteQuery = useQuery({ queryKey: ['lotes', id], queryFn: () => obterLote(id) });

  const mutation = useMutation({
    mutationFn: (geo: GeoJsonPolygon) => atualizarGeometriaLote(id, geo),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['lotes', id] });
      router.back();
    },
    onError: (err) => setErroSalvar(getErrorMessage(err, 'Não foi possível salvar a geometria.')),
  });

  async function escolherImagemDaPlanta() {
    const picked = await DocumentPicker.getDocumentAsync({ type: 'image/*', copyToCacheDirectory: true });
    if (picked.canceled || !picked.assets[0]) return;
    calibragem.escolherImagem(picked.assets[0]); // envia a imagem e já pede a sugestão da IA (SCRUM-100)
  }

  function aplicarCalibragem() {
    const overlay = calibragem.calibrar();
    if (overlay) {
      setImagemOverlay(overlay);
      setPoligonoSugerido(calibragem.obterPoligonoSugerido());
      setModo('editar');
    }
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {loteQuery.data?.identificacao ?? 'Geometria do lote'}
        </Text>
        {Platform.OS === 'web' && modo === 'editar' && (
          <Pressable onPress={() => setModo('calibrar')} style={styles.calibrarButton} hitSlop={8}>
            <MapPin size={16} color={colors.primary} />
            <Text style={styles.calibrarButtonText}>Calibrar planta</Text>
          </Pressable>
        )}
      </View>

      {loteQuery.isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : loteQuery.isError || !loteQuery.data ? (
        <View style={styles.center}>
          <Text style={styles.message}>Não foi possível carregar o lote.</Text>
          <Button mode="outlined" onPress={() => loteQuery.refetch()}>
            Tentar novamente
          </Button>
        </View>
      ) : modo === 'calibrar' ? (
        <View style={styles.calibragem}>
          {!calibragem.imagemUri ? (
            <View style={styles.center}>
              <Text style={styles.message}>
                Escolha a imagem da planta e marque 2 a 3 pontos com endereço/coordenada conhecidos.
              </Text>
              <Button mode="contained" onPress={escolherImagemDaPlanta}>
                Escolher imagem
              </Button>
              <Button mode="text" onPress={() => setModo('editar')}>
                Cancelar
              </Button>
            </View>
          ) : (
            <CalibragemImagem
              imagemUri={calibragem.imagemUri}
              tamanhoImagem={calibragem.tamanhoImagem}
              onMedirImagem={calibragem.setTamanhoImagem}
              pontos={calibragem.pontos}
              pontoPendente={calibragem.pontoPendente}
              onMarcarPonto={calibragem.setPontoPendente}
              onConfirmarPonto={calibragem.adicionarPonto}
              sugestao={calibragem.sugestao}
              sugestaoCarregando={calibragem.sugestaoCarregando}
              contornoSelecionado={calibragem.contornoSelecionado}
              onSelecionarContorno={calibragem.setContornoSelecionado}
            />
          )}

          <HelperText type="error" visible={calibragem.erro !== null}>
            {calibragem.erro}
          </HelperText>
          {calibragem.imagemUri && (
            <View style={[shared.stickyFooter, styles.footer]}>
              <Button
                mode="contained"
                disabled={calibragem.pontos.length < 2}
                onPress={aplicarCalibragem}
                contentStyle={styles.buttonContent}
              >
                Aplicar calibragem ({calibragem.pontos.length} ponto{calibragem.pontos.length === 1 ? '' : 's'})
              </Button>
            </View>
          )}
        </View>
      ) : (
        <>
          <PoligonoEditorMapa
            poligonoInicial={poligonoSugerido ?? loteQuery.data.geometria}
            imagemOverlay={imagemOverlay}
            onGeometriaChange={setGeometria}
          />
          <View style={[shared.stickyFooter, styles.footer]}>
            <HelperText type="error" visible={erroSalvar !== null}>
              {erroSalvar}
            </HelperText>
            <Button
              mode="contained"
              onPress={() => {
                setErroSalvar(null);
                if (geometria) mutation.mutate(geometria);
                else setErroSalvar('Desenhe o polígono do lote antes de salvar.');
              }}
              loading={mutation.isPending}
              disabled={mutation.isPending}
              contentStyle={styles.buttonContent}
              labelStyle={styles.buttonLabel}
            >
              Salvar geometria
            </Button>
          </View>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingHorizontal: 16,
    paddingTop: 20,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    flex: 1,
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  calibrarButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  calibrarButtonText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.primary,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  message: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.foreground,
    textAlign: 'center',
  },
  footer: {
    gap: 4,
  },
  buttonContent: {
    minHeight: 52,
  },
  buttonLabel: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
  },
  calibragem: {
    flex: 1,
  },
});
