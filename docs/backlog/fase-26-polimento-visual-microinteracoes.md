# Fase 26 — Polimento Visual & Microinterações

Entrega desta fase: pesquisa cuidadosa de que tipo de animação/partícula cabe no app (ponto de partida: a tela de login, especificamente a imagem de lotes — ideia é dar um movimento sutil nela), prototipada em 2-3 variações com GIF de cada, **validada explicitamente pelo usuário antes de qualquer integração real no app**. Esta fase é deliberadamente a última do roadmap numerado (depois da Fase 25 de segurança) não porque dependa dela — é puramente cosmético/exploratório, sem dependência técnica real com o resto do roadmap — mas para não competir por atenção com as fases que entregam funcionalidade real. Fecha a decisão D18 (biblioteca de animação/partículas) de `03-decisoes-tecnicas.md`.

**Regra de execução desta fase, conforme pedido explícito do usuário (2026-09-27): nenhuma animação entra no app de verdade sem aprovação explícita do usuário sobre o protótipo em GIF.** Não é uma sugestão de processo, é um bloqueio: `FASE26-IMPL-02` não começa sem essa aprovação registrada.

## Épico E26.1 — Fundamentos

### FASE26-EST-01-D1 / FASE26-EST-01-D2 — Estudo: bibliotecas de animação/partículas — teste comparativo das 3 opções
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** decidir a biblioteca de animação **por resultado prático**, não por trade-off teórico — critério confirmado pelo usuário (2026-09-27), mesmo padrão de D15: testar as 3, escolher a que rodar sem erro/travamento e ficar mais bonita, independente da curva de aprendizado de cada uma.
- **Conceitos a entender:** `react-native-reanimated` (animação declarativa na UI thread); Lottie (`lottie-react-native`, roda animação exportada do After Effects/Bodymovin); `react-native-skia` (motor de desenho 2D performático, permite partícula customizada); custo de performance de cada uma em device de entrada; suporte de cada uma no Expo for Web (mesmo dilema de D8/D9/D15) — mas aqui a resolução é empírica, não por comparação de documentação.
- **Material recomendado:** documentação oficial das 3 bibliotecas.
- **Exercício prático:** implementar a **mesma animação de teste** (ex. elemento flutuando/paralaxe leve) nas **3 bibliotecas**, cada uma nas duas plataformas (mobile e Expo for Web) — 6 execuções no total. Registrar erro/travamento encontrado (se houver) e avaliação visual comparativa.
- **Critério de conclusão:** as 3 opções testadas nas duas plataformas; D18 fechada com a que teve menos erro e melhor resultado visual — decisão registrada em `03-decisoes-tecnicas.md` com o motivo objetivo.
- **Paralelizável:** Sim.

## Épico E26.2 — Prototipagem e validação humana

### FASE26-IMPL-01 — Protótipos de animação para a tela de login (2-3 variações) + GIFs para validação
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** apresentar ao usuário 2-3 propostas concretas e visualizáveis de animação sutil na imagem de lotes da tela de login, para ele escolher (ou pedir ajuste, ou recusar todas) — **nada aqui é implementado no app principal ainda**.
- **Descrição:** protótipos isolados (branch própria ou tela de teste isolada, nunca direto na tela de login real usada em produção/demo) explorando variações de baixo custo visual e de performance — ex.: leve movimento de paralaxe ao mover o device/scroll, partículas discretas sugerindo "pontos" nos lotes do mapa da imagem, fade/pulse sutil de destaque em um lote; cada variação exportada como GIF curto (poucos segundos, mostrando o comportamento real, não um mockup estático) e anexada à descrição do PR de protótipo.
- **Pré-requisitos:** FASE26-EST-01-D1.
- **Dependências:** nenhuma além da tela de login já existente (Fase 3).
- **Resultado esperado:** PR de protótipo com 2-3 GIFs, um por variação, prontos para o usuário revisar e decidir.
- **Critérios de aceite:** cada GIF mostra o comportamento de fato rodando (não é uma animação CSS de mockup em ferramenta de design, é capturado do app/emulador rodando); PR **não é mesclado** até resposta do usuário sobre qual variação (se alguma) aprovar.
- **Paralelizável:** Não pode ser finalizada sem FASE26-EST-01.
- **Conhecimentos novos introduzidos:** captura de GIF de interação em device/emulador para revisão assíncrona.

## Épico E26.3 — Implementação aprovada

### FASE26-IMPL-02 — Implementação da animação aprovada na tela de login real
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** só a variação explicitamente aprovada pelo usuário entra na tela de login real do app — nunca uma escolha unilateral de dev.
- **Descrição:** implementação da variação aprovada (ou da versão ajustada pedida pelo usuário sobre um dos protótipos) na tela de login de verdade; GIF final do comportamento (rodando na tela real, não no protótipo isolado) incluído na descrição do PR, conforme pedido explícito do usuário; se a performance na tela real divergir do protótipo isolado (ex. mais elementos na tela real competindo por frame), qualquer ajuste de novo passa por validação antes de mesclar.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE26-IMPL-01 (aprovação explícita do usuário sobre uma variação).
- **Resultado esperado:** tela de login real com a animação aprovada, sem regressão de performance perceptível.
- **Critérios de aceite:** GIF do comportamento final anexado na descrição do PR; nenhuma variação não aprovada chega a este PR.
- **Paralelizável:** Não pode ser finalizada sem FASE26-IMPL-01 e aprovação explícita do usuário.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto em FASE26-EST-01.

#### Handoff (SCRUM-253)

- Usuário aprovou **F** (login) e **G** (splash) — ver comentário de aprovação no PR #47 (SCRUM-252, fechado sem merge, só protótipo). Esta task não empilha em cima da branch do protótipo: como o PR de protótipo nunca é mesclado, `feat/SCRUM-253-animacao-login-splash-aprovada` foi criada a partir da mesma base que SCRUM-252 usou (ponta de `feat/SCRUM-114-script-avaliacao-automatizada`), não da branch do protótipo — reinstala `react-native-reanimated`/`babel.config.js`/fecha D18 de novo (mesmo diff pequeno, já validado na 252).
- **Login** (`mobile/app/login.tsx`): variação F extraída para componente reutilizável `mobile/src/components/LoginHeroLotHighlight.tsx` (não ficou inline na tela) — um quadrado verde do tamanho de uma célula do grid (24×24, mesma malha do padrão SVG já existente no hero) pula entre 6 posições alinhadas à malha a cada ~900ms.
- **Splash** (`mobile/src/components/SplashAnimation.tsx`, reescrito): moldura+cruz do mark montam (estilo Switch), palavra "LotIAdo" cai em cascata letra a letra (estilo iFood), só depois o quadrado verde cai de fora do quadro e "bate" (squash) em cima do laranja — antes disso o Logo usava `Animated` (API nativa do RN) num fade+scale simples; agora usa `react-native-reanimated`, então essa tela passa a depender da mesma lib que o login. API do componente (`onFinish`) não mudou, `mobile/app/_layout.tsx` não precisou de alteração.
- GIF do comportamento final rodando na tela real (não no protótipo isolado) em `docs/design/screenshots/scrum-253-login-hero-real.gif` e `docs/design/screenshots/scrum-253-splash-real.gif`.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE26-EST-01 → FASE26-IMPL-01 (protótipos) → FASE26-IMPL-02 (implementação aprovada).
- **Dev 2:** FASE26-EST-01 (apoio/segunda opinião sobre as bibliotecas testadas).
- **Pontos de sincronização:** o ponto de sincronização real desta fase não é entre os devs, é com o usuário — `FASE26-IMPL-02` é bloqueada até aprovação explícita sobre `FASE26-IMPL-01`, não é um "paralelizável: sim" comum.
