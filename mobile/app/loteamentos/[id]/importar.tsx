import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import * as DocumentPicker from 'expo-document-picker';
import { Button, HelperText } from 'react-native-paper';
import { ArrowLeft, CheckCircle2, FileSpreadsheet } from 'lucide-react-native';

import {
  confirmarImportacaoCsv,
  previewImportacaoCsv,
  type CampoLote,
  type MapeamentoColunas,
  type ResultadoImportacao,
} from '../../../src/api/importacao';
import { getErrorMessage } from '../../../src/lib/errors';
import { colors, fonts } from '../../../src/theme/tokens';
import { shared } from '../../../src/theme/shared';

const CAMPOS: { campo: CampoLote; label: string; obrigatorio: boolean }[] = [
  { campo: 'identificacao', label: 'Identificação do lote', obrigatorio: true },
  { campo: 'quadra', label: 'Quadra', obrigatorio: false },
  { campo: 'area_m2', label: 'Área (m²)', obrigatorio: false },
  { campo: 'preco', label: 'Preço', obrigatorio: false },
];

export default function ImportarCsvScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [arquivo, setArquivo] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
  const [colunas, setColunas] = useState<string[]>([]);
  const [mapeamento, setMapeamento] = useState<MapeamentoColunas>({});
  const [resultado, setResultado] = useState<ResultadoImportacao | null>(null);
  const [error, setError] = useState<string | null>(null);

  const previewMutation = useMutation({
    mutationFn: (asset: DocumentPicker.DocumentPickerAsset) => previewImportacaoCsv(id, asset),
    onSuccess: (cabecalhos, asset) => {
      setArquivo(asset);
      setColunas(cabecalhos);
      setMapeamento({});
      setResultado(null);
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível ler o CSV.')),
  });

  const importMutation = useMutation({
    mutationFn: () => confirmarImportacaoCsv(id, arquivo!, mapeamento),
    onSuccess: async (res) => {
      setResultado(res);
      await queryClient.invalidateQueries({ queryKey: ['loteamentos', id, 'lotes'] });
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível importar o CSV.')),
  });

  async function escolherArquivo() {
    setError(null);
    const picked = await DocumentPicker.getDocumentAsync({
      type: ['text/csv', 'text/comma-separated-values', 'application/vnd.ms-excel', 'text/plain'],
      copyToCacheDirectory: true,
    });
    if (!picked.canceled && picked.assets[0]) {
      previewMutation.mutate(picked.assets[0]);
    }
  }

  function escolherColuna(campo: CampoLote, coluna: string | undefined) {
    setMapeamento((atual) => {
      const proximo = { ...atual };
      if (coluna === undefined) {
        delete proximo[campo];
      } else {
        proximo[campo] = coluna;
      }
      return proximo;
    });
  }

  const podeImportar = arquivo !== null && !!mapeamento.identificacao && resultado === null;

  return (
    <View style={styles.flex}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Importar lotes (CSV)</Text>
      </View>

      <ScrollView contentContainerStyle={styles.body} keyboardShouldPersistTaps="handled">
        <View style={[shared.cardSurface, styles.card]}>
          <Text style={styles.sectionTitle}>1. Arquivo</Text>
          <Text style={styles.hint}>Envie um CSV com cabeçalho na primeira linha. As colunas podem estar em qualquer ordem.</Text>
          <Button
            mode="outlined"
            icon={() => <FileSpreadsheet size={18} color={colors.primary} />}
            onPress={escolherArquivo}
            loading={previewMutation.isPending}
            disabled={previewMutation.isPending || importMutation.isPending}
          >
            {arquivo ? 'Trocar arquivo' : 'Escolher arquivo CSV'}
          </Button>
          {arquivo ? <Text style={styles.fileName}>{arquivo.name}</Text> : null}
        </View>

        {arquivo && colunas.length > 0 && resultado === null ? (
          <View style={[shared.cardSurface, styles.card]}>
            <Text style={styles.sectionTitle}>2. Associe as colunas</Text>
            <Text style={styles.hint}>Para cada campo do sistema, escolha a coluna correspondente do CSV.</Text>
            {CAMPOS.map(({ campo, label, obrigatorio }) => (
              <View key={campo} style={styles.campo}>
                <Text style={styles.campoLabel}>
                  {label}
                  {obrigatorio ? ' *' : ''}
                </Text>
                <View style={styles.chips}>
                  {!obrigatorio ? (
                    <Chip label="Não importar" active={mapeamento[campo] === undefined} onPress={() => escolherColuna(campo, undefined)} />
                  ) : null}
                  {colunas.map((coluna) => (
                    <Chip
                      key={coluna}
                      label={coluna}
                      active={mapeamento[campo] === coluna}
                      onPress={() => escolherColuna(campo, coluna)}
                    />
                  ))}
                </View>
              </View>
            ))}
          </View>
        ) : null}

        {resultado ? <ResultadoCard resultado={resultado} /> : null}

        <HelperText type="error" visible={error !== null}>
          {error}
        </HelperText>
      </ScrollView>

      <View style={shared.stickyFooter}>
        {resultado ? (
          <Button
            mode="contained"
            onPress={() => router.replace(`/loteamentos/${id}`)}
            contentStyle={styles.buttonContent}
            labelStyle={styles.buttonLabel}
          >
            Ver lotes
          </Button>
        ) : (
          <Button
            mode="contained"
            onPress={() => {
              setError(null);
              importMutation.mutate();
            }}
            loading={importMutation.isPending}
            disabled={!podeImportar || importMutation.isPending}
            contentStyle={styles.buttonContent}
            labelStyle={styles.buttonLabel}
          >
            Importar lotes
          </Button>
        )}
      </View>
    </View>
  );
}

function Chip({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={[styles.chip, active && styles.chipActive]}>
      <Text style={[styles.chipText, active && styles.chipTextActive]}>{label}</Text>
    </Pressable>
  );
}

function ResultadoCard({ resultado }: { resultado: ResultadoImportacao }) {
  return (
    <View style={[shared.cardSurface, styles.card]}>
      <View style={styles.resultadoHeader}>
        <CheckCircle2 size={20} color={colors.primary} />
        <Text style={styles.sectionTitle}>
          {resultado.importados} de {resultado.total_linhas} linhas importadas
        </Text>
      </View>
      {resultado.erros.length > 0 ? (
        <>
          <Text style={styles.hint}>As linhas abaixo não foram importadas; o restante foi salvo normalmente.</Text>
          {resultado.erros.map((erro) => (
            <Text key={`${erro.linha}-${erro.erro}`} style={styles.erroLinha}>
              Linha {erro.linha}: {erro.erro}
            </Text>
          ))}
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  flex: {
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
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  body: {
    flexGrow: 1,
    padding: 16,
    gap: 16,
  },
  card: {
    padding: 16,
    gap: 12,
  },
  sectionTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
  },
  hint: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
  },
  fileName: {
    fontFamily: fonts.bodyMedium,
    fontSize: 13,
    color: colors.foreground,
  },
  campo: {
    gap: 8,
  },
  campoLabel: {
    fontFamily: fonts.bodyMedium,
    fontSize: 14,
    color: colors.foreground,
  },
  chips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    height: 36,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.card,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipActive: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  chipText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.foreground,
  },
  chipTextActive: {
    color: colors.primaryForeground,
  },
  resultadoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  erroLinha: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.foreground,
  },
  buttonContent: {
    minHeight: 52,
  },
  buttonLabel: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
  },
});
