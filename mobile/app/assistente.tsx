import { useRef, useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, TextInput as RNTextInput, View } from 'react-native';
import { router } from 'expo-router';
import { useMutation } from '@tanstack/react-query';
import { ActivityIndicator } from 'react-native-paper';
import { ArrowLeft, ArrowUp, Check, ShieldAlert, Sparkles, X } from 'lucide-react-native';

import { confirmarAcao, perguntarAgente, type ConfirmacaoAcaoPendente } from '../src/api/agente';
import { getErrorMessage } from '../src/lib/errors';
import { OFFLINE_MESSAGE, useIsOnline } from '../src/lib/useIsOnline';
import { colors, fonts, radius } from '../src/theme/tokens';

type AcaoPendente =
  | { tipo: 'pergunta'; texto: string }
  | { tipo: 'confirmar'; confirmacaoId: string; aprovado: boolean; mensagemId: string };

type Mensagem =
  | { id: string; papel: 'usuario'; texto: string }
  | { id: string; papel: 'assistente'; texto: string }
  | { id: string; papel: 'confirmacao'; confirmacao: ConfirmacaoAcaoPendente; status: 'pendente' | 'aprovada' | 'recusada' }
  | { id: string; papel: 'erro'; texto: string; acao: AcaoPendente };

const SUGESTAO = 'Quais lotes de esquina abaixo de 100 mil?';

function Avatar() {
  return (
    <View style={styles.avatar}>
      <Sparkles size={16} color={colors.accentForeground} />
    </View>
  );
}

function formatarArgumentos(argumentos: Record<string, unknown>): { chave: string; valor: string }[] {
  return Object.entries(argumentos).map(([chave, valor]) => ({
    chave: chave.replace(/_/g, ' '),
    valor: String(valor),
  }));
}

export default function AssistenteScreen() {
  const isOnline = useIsOnline();
  const [texto, setTexto] = useState('');
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const scrollRef = useRef<ScrollView>(null);

  const temConfirmacaoPendente = mensagens.some((msg) => msg.papel === 'confirmacao' && msg.status === 'pendente');

  function processarResultado(resultado: { resposta: string | null; confirmacao: ConfirmacaoAcaoPendente | null }) {
    if (resultado.confirmacao) {
      setMensagens((atual) => [
        ...atual,
        { id: `${Date.now()}-confirmacao`, papel: 'confirmacao', confirmacao: resultado.confirmacao!, status: 'pendente' },
      ]);
      return;
    }
    setMensagens((atual) => [
      ...atual,
      {
        id: `${Date.now()}-assistente`,
        papel: 'assistente',
        texto: resultado.resposta ?? 'Não consegui gerar uma resposta para essa pergunta.',
      },
    ]);
  }

  const perguntaMutation = useMutation({
    mutationFn: (pergunta: string) => perguntarAgente(pergunta),
    onSuccess: processarResultado,
    onError: (err, pergunta) => {
      setMensagens((atual) => [
        ...atual,
        {
          id: `${Date.now()}-erro`,
          papel: 'erro',
          texto: getErrorMessage(err, 'Não foi possível obter uma resposta.'),
          acao: { tipo: 'pergunta', texto: pergunta },
        },
      ]);
    },
  });

  const confirmarMutation = useMutation({
    mutationFn: ({ confirmacaoId, aprovado }: { confirmacaoId: string; aprovado: boolean; mensagemId: string }) =>
      confirmarAcao(confirmacaoId, aprovado),
    onSuccess: (resultado, { aprovado, mensagemId }) => {
      setMensagens((atual) =>
        atual.map((msg) =>
          msg.id === mensagemId && msg.papel === 'confirmacao'
            ? { ...msg, status: aprovado ? 'aprovada' : 'recusada' }
            : msg,
        ),
      );
      processarResultado(resultado);
    },
    onError: (err, { confirmacaoId, aprovado, mensagemId }) => {
      setMensagens((atual) => [
        ...atual,
        {
          id: `${Date.now()}-erro`,
          papel: 'erro',
          texto: getErrorMessage(err, 'Não foi possível processar a confirmação.'),
          acao: { tipo: 'confirmar', confirmacaoId, aprovado, mensagemId },
        },
      ]);
    },
  });

  function enviar(pergunta: string) {
    const limpa = pergunta.trim();
    if (limpa === '' || perguntaMutation.isPending || temConfirmacaoPendente) return;
    setMensagens((atual) => [...atual, { id: `${Date.now()}-usuario`, papel: 'usuario', texto: limpa }]);
    setTexto('');
    perguntaMutation.mutate(limpa);
  }

  function decidir(mensagemId: string, confirmacaoId: string, aprovado: boolean) {
    if (confirmarMutation.isPending) return;
    confirmarMutation.mutate({ confirmacaoId, aprovado, mensagemId });
  }

  function repetirAcao(acao: AcaoPendente) {
    if (acao.tipo === 'pergunta') {
      perguntaMutation.mutate(acao.texto);
    } else {
      confirmarMutation.mutate({ confirmacaoId: acao.confirmacaoId, aprovado: acao.aprovado, mensagemId: acao.mensagemId });
    }
  }

  const carregando = perguntaMutation.isPending || confirmarMutation.isPending;

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
              Faça uma pergunta ou peça uma ação sobre os loteamentos, lotes, clientes e vendas cadastrados.
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
                  <Pressable onPress={() => repetirAcao(msg.acao)} hitSlop={6}>
                    <Text style={styles.retryText}>Tentar novamente</Text>
                  </Pressable>
                </View>
              </View>
            );
          }

          if (msg.papel === 'confirmacao') {
            const { confirmacao, status } = msg;
            return (
              <View key={msg.id} style={styles.rowAssistente}>
                <Avatar />
                <View style={styles.colunaAssistente}>
                  <View style={styles.confirmacaoCard}>
                    <View style={styles.confirmacaoHeader}>
                      <ShieldAlert size={16} color={colors.primary} />
                      <Text style={styles.confirmacaoTitulo}>Confirmação necessária</Text>
                    </View>
                    <Text style={styles.confirmacaoDescricao}>{confirmacao.descricao}</Text>
                    <View style={styles.confirmacaoArgumentos}>
                      {formatarArgumentos(confirmacao.argumentos).map(({ chave, valor }) => (
                        <Text key={chave} style={styles.confirmacaoArgumento}>
                          <Text style={styles.confirmacaoArgumentoChave}>{chave}: </Text>
                          {valor}
                        </Text>
                      ))}
                    </View>

                    {status === 'pendente' ? (
                      <View style={styles.confirmacaoBotoes}>
                        <Pressable
                          style={styles.botaoRecusar}
                          onPress={() => decidir(msg.id, confirmacao.confirmacao_id, false)}
                          disabled={confirmarMutation.isPending}
                        >
                          <X size={16} color={colors.destructive} />
                          <Text style={styles.botaoRecusarTexto}>Recusar</Text>
                        </Pressable>
                        <Pressable
                          style={styles.botaoAceitar}
                          onPress={() => decidir(msg.id, confirmacao.confirmacao_id, true)}
                          disabled={confirmarMutation.isPending}
                        >
                          <Check size={16} color={colors.accentForeground} />
                          <Text style={styles.botaoAceitarTexto}>Aceitar</Text>
                        </Pressable>
                      </View>
                    ) : (
                      <Text style={status === 'aprovada' ? styles.confirmacaoStatusAprovada : styles.confirmacaoStatusRecusada}>
                        {status === 'aprovada' ? 'Ação aprovada' : 'Ação recusada'}
                      </Text>
                    )}
                  </View>
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
              </View>
            </View>
          );
        })}

        {carregando ? (
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
        {temConfirmacaoPendente ? (
          <Text style={styles.offlineText}>Responda à confirmação acima antes de continuar.</Text>
        ) : null}
        <View style={styles.composerRow}>
          <RNTextInput
            value={texto}
            onChangeText={setTexto}
            placeholder="Escreva sua pergunta…"
            placeholderTextColor={colors.mutedForeground}
            style={styles.composerInput}
            multiline
            editable={isOnline && !temConfirmacaoPendente}
          />
          <Pressable
            style={[
              styles.sendButton,
              (texto.trim() === '' || perguntaMutation.isPending || !isOnline || temConfirmacaoPendente) &&
                styles.sendButtonDisabled,
            ]}
            onPress={() => enviar(texto)}
            disabled={texto.trim() === '' || perguntaMutation.isPending || !isOnline || temConfirmacaoPendente}
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
  confirmacaoCard: {
    alignSelf: 'flex-start',
    width: '100%',
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.primarySoft,
    borderRadius: radius.lg,
    padding: 12,
    gap: 8,
  },
  confirmacaoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  confirmacaoTitulo: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.primary,
  },
  confirmacaoDescricao: {
    fontFamily: fonts.body,
    fontSize: 14,
    lineHeight: 20,
    color: colors.foreground,
  },
  confirmacaoArgumentos: {
    gap: 2,
  },
  confirmacaoArgumento: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.mutedForeground,
  },
  confirmacaoArgumentoChave: {
    fontFamily: fonts.bodySemiBold,
    color: colors.mutedForeground,
  },
  confirmacaoBotoes: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 4,
  },
  botaoRecusar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    borderWidth: 1,
    borderColor: colors.destructive,
    borderRadius: radius.md,
    paddingVertical: 9,
  },
  botaoRecusarTexto: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.destructive,
  },
  botaoAceitar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: colors.accent,
    borderRadius: radius.md,
    paddingVertical: 9,
  },
  botaoAceitarTexto: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.accentForeground,
  },
  confirmacaoStatusAprovada: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.accent,
  },
  confirmacaoStatusRecusada: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.destructive,
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
