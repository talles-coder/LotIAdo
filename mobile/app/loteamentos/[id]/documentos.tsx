import { useState } from 'react';
import { FlatList, Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as DocumentPicker from 'expo-document-picker';
import { ActivityIndicator, Button, HelperText } from 'react-native-paper';
import { ArrowLeft, Download, FileText, Trash2, Upload } from 'lucide-react-native';

import {
  enviarDocumento,
  listarDocumentos,
  obterUrlAssinadaDocumento,
  removerDocumento,
  type Documento,
} from '../../../src/api/documentos';
import { getErrorMessage } from '../../../src/lib/errors';
import { colors, fonts } from '../../../src/theme/tokens';
import { shared } from '../../../src/theme/shared';

function formatarTamanho(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentosDoLoteamentoScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const documentosQuery = useQuery({
    queryKey: ['loteamentos', id, 'documentos'],
    queryFn: () => listarDocumentos({ loteamentoId: id }),
  });

  const uploadMutation = useMutation({
    mutationFn: (asset: DocumentPicker.DocumentPickerAsset) =>
      enviarDocumento(asset, { loteamentoId: id }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['loteamentos', id, 'documentos'] });
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível enviar o documento.')),
  });

  const removerMutation = useMutation({
    mutationFn: (documentoId: string) => removerDocumento(documentoId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['loteamentos', id, 'documentos'] });
    },
    onError: (err) => setError(getErrorMessage(err, 'Não foi possível remover o documento.')),
  });

  async function escolherArquivo() {
    setError(null);
    const picked = await DocumentPicker.getDocumentAsync({ copyToCacheDirectory: true });
    if (!picked.canceled && picked.assets[0]) {
      uploadMutation.mutate(picked.assets[0]);
    }
  }

  async function abrirDocumento(documento: Documento) {
    setError(null);
    try {
      const url = await obterUrlAssinadaDocumento(documento.id);
      await Linking.openURL(url);
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível abrir o documento.'));
    }
  }

  return (
    <View style={styles.flex}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Documentos</Text>
      </View>

      <View style={styles.body}>
        <Button
          mode="outlined"
          icon={() => <Upload size={18} color={colors.primary} />}
          onPress={escolherArquivo}
          loading={uploadMutation.isPending}
          disabled={uploadMutation.isPending}
          style={styles.uploadButton}
        >
          Enviar documento
        </Button>

        <HelperText type="error" visible={error !== null}>
          {error}
        </HelperText>

        {documentosQuery.isLoading ? (
          <View style={styles.center}>
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : documentosQuery.isError ? (
          <View style={styles.center}>
            <Text style={styles.errorText}>Não foi possível carregar os documentos.</Text>
            <Button mode="outlined" onPress={() => documentosQuery.refetch()}>
              Tentar novamente
            </Button>
          </View>
        ) : (
          <FlatList
            data={documentosQuery.data}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.list}
            ListEmptyComponent={<Text style={styles.empty}>Nenhum documento enviado ainda.</Text>}
            renderItem={({ item }: { item: Documento }) => (
              <View style={[shared.cardSurface, styles.card]}>
                <FileText size={20} color={colors.mutedForeground} />
                <View style={styles.cardBody}>
                  <Text style={styles.cardTitle} numberOfLines={1}>
                    {item.nome}
                  </Text>
                  <Text style={styles.cardSubtitle}>{formatarTamanho(item.tamanho_bytes)}</Text>
                </View>
                <Pressable onPress={() => abrirDocumento(item)} style={styles.iconButton} hitSlop={8}>
                  <Download size={18} color={colors.foreground} />
                </Pressable>
                <Pressable
                  onPress={() => removerMutation.mutate(item.id)}
                  style={styles.iconButton}
                  hitSlop={8}
                  disabled={removerMutation.isPending}
                >
                  <Trash2 size={18} color={colors.destructive} />
                </Pressable>
              </View>
            )}
          />
        )}
      </View>
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
    flex: 1,
    padding: 16,
    gap: 8,
  },
  uploadButton: {
    alignSelf: 'flex-start',
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 12,
  },
  list: {
    gap: 10,
    paddingTop: 8,
  },
  card: {
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  cardBody: {
    flex: 1,
  },
  cardTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 15,
    color: colors.foreground,
  },
  cardSubtitle: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
    marginTop: 2,
  },
  iconButton: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  empty: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.mutedForeground,
    textAlign: 'center',
    marginTop: 32,
  },
  errorText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.foreground,
    textAlign: 'center',
  },
});
