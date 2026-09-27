import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { Button, HelperText, TextInput } from 'react-native-paper';
import { ArrowLeft, FileText, Sparkles } from 'lucide-react-native';

import { perguntar, type PerguntaResponse } from '../src/api/rag';
import { getErrorMessage } from '../src/lib/errors';
import { OFFLINE_MESSAGE, useIsOnline } from '../src/lib/useIsOnline';
import { colors, fonts, radius } from '../src/theme/tokens';
import { shared } from '../src/theme/shared';

export default function AssistenteScreen() {
  const isOnline = useIsOnline();
  const [pergunta, setPergunta] = useState('');
  const [resultado, setResultado] = useState<PerguntaResponse | null>(null);

  const mutation = useMutation({
    mutationFn: () => perguntar({ pergunta: pergunta.trim() }),
    onSuccess: (data) => setResultado(data),
  });

  function handlePerguntar() {
    if (pergunta.trim() === '') return;
    mutation.mutate();
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <Text style={styles.headerTitle}>Pergunte ao LotIAdo</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={styles.searchWrapper}>
          <TextInput
            mode="outlined"
            placeholder="Ex.: Quais lotes de esquina abaixo de 100 mil?"
            value={pergunta}
            onChangeText={setPergunta}
            style={styles.input}
            outlineStyle={styles.inputOutline}
            multiline
          />
        </View>

        {mutation.isPending ? (
          <View style={[shared.cardSurface, styles.answerCard]}>
            <Text style={styles.loadingText}>Buscando resposta…</Text>
          </View>
        ) : null}

        {mutation.isError ? (
          <HelperText type="error" visible style={styles.error}>
            {getErrorMessage(mutation.error, 'Não foi possível obter uma resposta.')}
          </HelperText>
        ) : null}

        {resultado && !mutation.isPending ? (
          <>
            <View style={[styles.answerBanner]}>
              <View style={styles.answerIconWrap}>
                <Sparkles size={18} color={colors.accentForeground} />
              </View>
              <Text style={styles.answerText}>{resultado.resposta}</Text>
            </View>

            {resultado.fontes.length > 0 ? (
              <View style={styles.sourcesSection}>
                <Text style={styles.sourcesTitle}>Fontes</Text>
                {resultado.fontes.map((fonte, index) => (
                  <View key={`${fonte.documento_id}-${index}`} style={[shared.cardSurface, styles.sourceCard]}>
                    <View style={styles.sourceHeader}>
                      <FileText size={14} color={colors.mutedForeground} />
                      <Text style={styles.sourceNome}>{fonte.documento_nome}</Text>
                    </View>
                    <Text style={styles.sourceTrecho}>{fonte.trecho}</Text>
                  </View>
                ))}
              </View>
            ) : null}
          </>
        ) : null}
      </ScrollView>

      <View style={[shared.stickyFooter, styles.footer]}>
        <HelperText type="error" visible={!isOnline} style={styles.footerError}>
          {OFFLINE_MESSAGE}
        </HelperText>
        <Button
          mode="contained"
          onPress={handlePerguntar}
          loading={mutation.isPending}
          disabled={mutation.isPending || pergunta.trim() === '' || !isOnline}
          contentStyle={styles.buttonContent}
          labelStyle={styles.buttonLabel}
        >
          Perguntar
        </Button>
      </View>
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
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  scroll: {
    padding: 16,
    paddingBottom: 28,
    gap: 16,
  },
  searchWrapper: {
    marginTop: 4,
  },
  input: {
    backgroundColor: colors.card,
  },
  inputOutline: {
    borderRadius: radius.lg,
  },
  answerCard: {
    padding: 16,
  },
  loadingText: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.mutedForeground,
  },
  error: {
    paddingHorizontal: 0,
  },
  answerBanner: {
    borderRadius: radius.xl,
    backgroundColor: colors.earth,
    padding: 16,
    flexDirection: 'row',
    gap: 12,
  },
  answerIconWrap: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  answerText: {
    flex: 1,
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 20,
    color: colors.earthForeground,
  },
  sourcesSection: {
    gap: 10,
  },
  sourcesTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.foreground,
  },
  sourceCard: {
    padding: 12,
    gap: 6,
  },
  sourceHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sourceNome: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.foreground,
  },
  sourceTrecho: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
    lineHeight: 18,
  },
  footer: {
    gap: 4,
  },
  footerError: {
    paddingHorizontal: 0,
  },
  buttonContent: {
    minHeight: 52,
  },
  buttonLabel: {
    fontFamily: fonts.displayBold,
    fontSize: 16,
  },
});
