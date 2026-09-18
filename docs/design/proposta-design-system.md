# Design System do App Hope (mobile + web)

✅ **Decidido.** Biblioteca de componentes: (A) React Native Paper (D9 em [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md)). Identidade visual (cor/tipografia/componentes): gerada no Lovable a partir de [lovable-brief.md](lovable-brief.md) e mapeada em detalhe em **[lovable-mapeamento.md](lovable-mapeamento.md) — fonte de verdade dos tokens**. Este documento cobre a decisão de biblioteca e como ela recebe os tokens do Lovable.

## D9 — Biblioteca de componentes multiplataforma

**Opções:**
- (A) React Native Paper (Material Design 3, mantida pela Callstack) — **escolhida**.
- (B) Tamagui (tokens + compilador, pensado para nativo+web desde a raiz).
- (C) Sem biblioteca — componentes próprios simples sobre `View`/`Pressable`/`Text`.

| | (A) React Native Paper | (B) Tamagui | (C) Componentes próprios |
|---|---|---|---|
| Vantagens | Setup rápido; acessibilidade (alvos de toque, screen reader) já resolvida; madura desde 2017; tema MD3 aceita cores/fontes customizadas via `MD3Theme`, então os tokens do Lovable entram sem fork da lib | Melhor caso de uso para web como alvo de primeira classe (D2/Fase 5); tokens nativos | Controle total; zero dependência |
| Desvantagens | Web via RN Web é suportado mas não é o caso de uso mais testado da lib | Setup mais pesado (config + compilador); curva de aprendizado maior | Reinventa botão, input, modal, etc. — atrasa a Fase 3 sem ganho de aprendizado central para o projeto |
| Custo | Zero | Zero | Zero |
| Impacto no aprendizado | Médio | Médio-alto (concentrado em ferramenta, não em domínio) | Baixo |

**Decidido:** (A). Reavaliar para (B) Tamagui só se a Fase 5 (Expo for Web) expuser limitação real de estilização compartilhada — mesmo critério usado em D8 para o wrapper de mapa.

## Como os tokens do Lovable entram no Paper

- Tema MD3 customizado em `mobile/src/theme/` — cores mapeadas 1:1 pra `MD3Theme.colors` (`primary`, `onPrimary`, `secondary`, `background`, `surface`, `error`, etc.), fontes via `configureFonts` (Outfit pro `displayLarge`/`headlineLarge`/etc., Figtree pro resto).
- Componentes que o Paper não cobre no mesmo espírito do repo Lovable (ex.: `Logo`, `StatusBadge` com dot) são implementados como componentes próprios em `mobile/src/components/`, usando os tokens do tema — nunca cor solta.
- Ver [lovable-mapeamento.md](lovable-mapeamento.md) pra tabela completa de cores (hex), tipografia, raio, sombra e padrões de tela.

## Padrões de tela a reaproveitar (mobile → web)

1. **Card de lote** com `StatusBadge` — mesmo componente na lista (Fase 3) e, futuramente, no board kanban do backoffice (Fase 5).
2. **Barra de ação fixa no rodapé** na tela de detalhe do lote (mobile) — conteúdo muda por status, ver `lovable-mapeamento.md`.
3. **Empty state ilustrado** (não só "nenhum resultado") para listas vazias — lote sem reservas, cliente sem histórico, etc. (ainda não mapeado no Lovable — ao chegar, seguir a mesma paleta cream/terracota).
