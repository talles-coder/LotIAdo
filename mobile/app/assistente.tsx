import { useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput as RNTextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { ActivityIndicator } from 'react-native-paper';
import { ArrowLeft, ArrowUp, FileText, Sparkles } from 'lucide-react-native';

import { perguntar, type FonteResposta } from '../src/api/rag';
import { getErrorMessage } from '../src/lib/errors';
import { OFFLINE_MESSAGE, useIsOnline } from '../src/lib/useIsOnline';
import { colors, fonts, radius } from '../src/theme/tokens';

type Mensagem =
  | { id: string; papel: 'usuario'; texto: string }
  | { id: string; papel: 'assistente'; texto: string; fontes: FonteResposta[] }
  | { id: string; papel: 'erro'; texto: string; perguntaOriginal: string };

const SUGESTAO = 'Quais lotes de esquina abaixo de 100 mil?';

function Avatar() {
  return (
    <View style={styles.avatar}>
      <Sparkles size={16} color={colors.accentForeground} />
    </View>
  );
}

export default function AssistenteScreen() {
  const isOnline = useIsOnline();
  const [texto, setTexto] = useState('');
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const scrollRef = useRef<ScrollView>(null);

  const mutation = useMutation({
    mutationFn: (pergunta: string) => perguntar({ pergunta }),
    onSuccess: (data) => {
      setMensagens((atual) => [
        ...atual,
        { id: `${Date.now()}-assistente`, papel: 'assistente', texto: data.resposta, fontes: data.fontes },
      ]);
    },
    onError: (err, pergunta) => {
      setMensagens((atual) => [
        ...atual,
        {
          id: `${Date.now()}-erro`,
          papel: 'erro',
          texto: getErrorMessage(err, 'Não foi possível obter uma resposta.'),
          perguntaOriginal: pergunta,
        },
      ]);
    },
  });

  function enviar(pergunta: string) {
    const limpa = pergunta.trim();
    if (limpa === '' || mutation.isPending) return;
    setMensagens((atual) => [...atual, { id: `${Date.now()}-usuario`, papel: 'usuario', texto: limpa }]);
    setTexto('');
    mutation.mutate(limpa);
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} style={styles.backButton} hitSlop={8}>
          <ArrowLeft size={22} color={colors.foreground} />
        </Pressable>
        <View style={styles.headerAvatar}>
          <Sparkles size={16} color={colors.accentForeground} />
        </View>
        <Text style={styles.headerTitle}>Pergunte ao LotIAdo</Text>
      </View>

      <ScrollView
        ref={scrollRef}
        style={styles.scrollFlex}
        contentContainerStyle={styles.scroll}
        onContentSizeChange={() => scrollRef.current?.scrollToEnd({ animated: true })}
      >
        {mensagens.length === 0 ? (
          <View style={styles.welcome}>
            <View style={styles.welcomeAvatar}>
              <Sparkles size={26} color={colors.accentForeground} />
            </View>
            <Text style={styles.welcomeTitle}>Pergunte ao LotIAdo</Text>
            <Text style={styles.welcomeSubtitle}>
              Faça uma pergunta sobre os loteamentos, lotes e documentos cadastrados.
            </Text>
            <Pressable style={styles.suggestion} onPress={() => enviar(SUGESTAO)}>
              <Text style={styles.suggestionText}>"{SUGESTAO}"</Text>
            </Pressable>
          </View>
        ) : null}

        {mensagens.map((msg) => {
          if (msg.papel === 'usuario') {
            return (
              <View key={msg.id} style={styles.rowUsuario}>
                <View style={styles.bolhaUsuario}>
                  <Text style={styles.textoUsuario}>{msg.texto}</Text>
                </View>
              </View>
            );
          }

          if (msg.papel === 'erro') {
            return (
              <View key={msg.id} style={styles.rowAssistente}>
                <Avatar />
                <View style={styles.colunaAssistente}>
                  <View style={styles.bolhaErro}>
                    <Text style={styles.textoErro}>{msg.texto}</Text>
                  </View>
                  <Pressable onPress={() => enviar(msg.perguntaOriginal)} hitSlop={6}>
                    <Text style={styles.retryText}>Tentar novamente</Text>
                  </Pressable>
                </View>
              </View>
            );
          }

          return (
            <View key={msg.id} style={styles.rowAssistente}>
              <Avatar />
              <View style={styles.colunaAssistente}>
                <View style={styles.bolhaAssistente}>
                  <Text style={styles.textoAssistente}>{msg.texto}</Text>
                </View>
                {msg.fontes.length > 0 ? (
                  <View style={styles.sourcesSection}>
                    {msg.fontes.map((fonte, index) => (
                      <View key={`${fonte.documento_id}-${index}`} style={styles.sourceCard}>
                        <FileText size={13} color={colors.mutedForeground} />
                        <View style={styles.sourceTextWrap}>
                          <Text style={styles.sourceNome}>{fonte.documento_nome}</Text>
                          <Text style={styles.sourceTrecho} numberOfLines={2}>
                            {fonte.trecho}
                          </Text>
                        </View>
                      </View>
                    ))}
                  </View>
                ) : null}
              </View>
            </View>
          );
        })}

        {mutation.isPending ? (
          <View style={styles.rowAssistente}>
            <Avatar />
            <View style={[styles.bolhaAssistente, styles.bolhaCarregando]}>
              <ActivityIndicator size={16} color={colors.earthForeground} />
            </View>
          </View>
        ) : null}
      </ScrollView>

      <View style={styles.composer}>
        {!isOnline ? <Text style={styles.offlineText}>{OFFLINE_MESSAGE}</Text> : null}
        <View style={styles.composerRow}>
          <RNTextInput
            value={texto}
            onChangeText={setTexto}
            placeholder="Escreva sua pergunta…"
            placeholderTextColor={colors.mutedForeground}
            style={styles.composerInput}
            multiline
            editable={isOnline}
          />
          <Pressable
            style={[styles.sendButton, (texto.trim() === '' || mutation.isPending || !isOnline) && styles.sendButtonDisabled]}
            onPress={() => enviar(texto)}
            disabled={texto.trim() === '' || mutation.isPending || !isOnline}
            hitSlop={6}
          >
            <ArrowUp size={20} color={colors.primaryForeground} />
          </Pressable>
        </View>
      </View>
    </KeyboardAvoidingView>
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
  headerAvatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 17,
    color: colors.foreground,
  },
  scrollFlex: {
    flex: 1,
  },
  scroll: {
    flexGrow: 1,
    padding: 16,
    gap: 14,
  },
  welcome: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingVertical: 40,
    gap: 6,
  },
  welcomeAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  welcomeTitle: {
    fontFamily: fonts.display,
    fontSize: 19,
    color: colors.foreground,
  },
  welcomeSubtitle: {
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.mutedForeground,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 12,
  },
  suggestion: {
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.card,
    borderRadius: radius.full,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  suggestionText: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.mutedForeground,
  },
  rowUsuario: {
    alignItems: 'flex-end',
  },
  bolhaUsuario: {
    maxWidth: '82%',
    backgroundColor: colors.primary,
    borderRadius: radius.xl,
    borderBottomRightRadius: 4,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  textoUsuario: {
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 20,
    color: colors.primaryForeground,
  },
  rowAssistente: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    maxWidth: '92%',
  },
  avatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  colunaAssistente: {
    flex: 1,
    gap: 8,
  },
  bolhaAssistente: {
    alignSelf: 'flex-start',
    backgroundColor: colors.earth,
    borderRadius: radius.xl,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  bolhaCarregando: {
    paddingVertical: 12,
  },
  textoAssistente: {
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 20,
    color: colors.earthForeground,
  },
  bolhaErro: {
    alignSelf: 'flex-start',
    backgroundColor: colors.muted,
    borderRadius: radius.xl,
    borderBottomLeftRadius: 4,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  textoErro: {
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 20,
    color: colors.destructive,
  },
  retryText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.primary,
    marginLeft: 4,
  },
  sourcesSection: {
    gap: 6,
  },
  sourceCard: {
    flexDirection: 'row',
    gap: 8,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: 10,
  },
  sourceTextWrap: {
    flex: 1,
  },
  sourceNome: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
    color: colors.foreground,
  },
  sourceTrecho: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
    marginTop: 1,
  },
  composer: {
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.card,
    paddingHorizontal: 12,
    paddingTop: 10,
    paddingBottom: 12,
  },
  offlineText: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.destructive,
    marginBottom: 6,
    marginLeft: 4,
  },
  composerRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
  },
  composerInput: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    backgroundColor: colors.muted,
    borderRadius: radius.xl,
    paddingHorizontal: 16,
    paddingVertical: 11,
    fontFamily: fonts.body,
    fontSize: 14,
    color: colors.foreground,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: colors.border,
  },
});
