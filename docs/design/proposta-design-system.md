# Proposta — Design System do App Hope (mobile + web)

✅ **Validado com o time — opção (A) React Native Paper.** Registrado como D9 em [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md). Este documento mantém o detalhe da comparação e os padrões de tela usados como referência para FASE3-IMPL-01 (SCRUM-63).

## D9 — Biblioteca de componentes multiplataforma

**Opções:**
- (A) React Native Paper (Material Design 3, mantida pela Callstack).
- (B) Tamagui (tokens + compilador, pensado para nativo+web desde a raiz).
- (C) Sem biblioteca — componentes próprios simples sobre `View`/`Pressable`/`Text`.

| | (A) React Native Paper | (B) Tamagui | (C) Componentes próprios |
|---|---|---|---|
| Vantagens | Setup rápido; acessibilidade (alvos de toque, screen reader) já resolvida; madura desde 2017 | Melhor caso de uso para web como alvo de primeira classe (D2/Fase 5); tokens nativos | Controle total; zero dependência; aprendizado direto de estilização RN |
| Desvantagens | Web via RN Web é suportado mas não é o caso de uso mais testado da lib | Setup mais pesado (config + compilador); curva de aprendizado maior | Reinventa botão, input, modal, etc. — atrasa a Fase 3 sem ganho de aprendizado central para o projeto |
| Custo | Zero | Zero | Zero |
| Impacto no aprendizado | Médio | Médio-alto (mas concentrado em ferramenta, não em domínio) | Baixo (não é o foco do projeto) |

**Decidido:** (A) React Native Paper para a Fase 3. Foco do projeto é domínio + IA, não profundidade em design system — Paper resolve componentes básicos (lista, botão, badge, input) rápido e com acessibilidade de graça. Reavaliar para (B) Tamagui só se a Fase 5 (Expo for Web) expuser limitação real de estilização compartilhada — mesmo critério usado em D8 para o wrapper de mapa ("se mostrar instável, cair para plano B").

## Tokens propostos (cores semânticas)

Sem gerar paleta de marca (fora de escopo de portfólio técnico), mas com **papéis semânticos nomeados** desde já, inspirado no padrão tokenizado do design system da ZAP Imóveis (ver referências):

- `status.disponivel`, `status.reservado`, `status.vendido`, `status.bloqueado` — cor + label, nunca só cor (acessibilidade).
- `surface.primary`, `surface.secondary` — fundo de card vs. fundo de tela.
- `action.primary`, `action.danger` — botão de ação principal (reservar/vender) vs. ação destrutiva (cancelar).

Esses nomes (não os valores hex) são o que deve entrar em código na Fase 3 — os valores exatos podem ser ajustados sem quebrar nenhum componente que já os referencia.

## Padrões de tela a reaproveitar (mobile → web)

1. **Card de lote** com badge de status — mesmo componente na lista (Fase 3) e, futuramente, no board kanban do backoffice (Fase 5).
2. **Barra de ação fixa no rodapé** na tela de detalhe do lote (mobile) — ações visíveis dependem do status atual (regra de transição da Fase 1), como já é critério de aceite de FASE3-IMPL-03.
3. **Empty state ilustrado** (não só "nenhum resultado") para listas vazias — lote sem reservas, cliente sem histórico, etc.

