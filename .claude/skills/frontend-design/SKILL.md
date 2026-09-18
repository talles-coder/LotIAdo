---
name: frontend-design
description: Padrões visuais, referências e processo para qualquer tela nova ou alterada (mobile Expo ou backoffice web) do projeto LotIAdo
type: code-review
trigger: [create-ui, edit-ui, create-screen, edit-screen]
applies-to: ["mobile/app/**/*.tsx", "mobile/src/components/**/*.tsx", "mobile/src/theme/**/*.ts", "backoffice/**/*.tsx"]
---

# Frontend/UI — Padrões do Projeto LotIAdo

Esta Skill se carrega ao criar/editar telas ou componentes visuais (mobile Expo ou backoffice web). **A identidade visual já está decidida — isto não é sobre inventar um novo design, é sobre aplicar fielmente o que já existe.**

## Fonte da verdade (nessa ordem)

1. **[docs/design/lovable-mapeamento.md](../../../docs/design/lovable-mapeamento.md)** — tokens (cor, tipografia, raio, sombra, ícones) e padrões de tela mapeados. Não inventar cor/fonte/componente fora daqui.
2. **[docs/design/screenshots/lovable-reference/](../../../docs/design/screenshots/lovable-reference/)** — print de cada tela do repo gerado no Lovable ([talles-coder/lotiado-gest-o-imobili-ria-inteligente](https://github.com/talles-coder/lotiado-gest-o-imobili-ria-inteligente)), capturado do app rodando de verdade (não é mockup solto). **Sempre olhe o print da tela equivalente antes de implementar** — layout, hierarquia, espaçamento, o que é fixo (header/footer) vs. rolável.
3. **[docs/design/screenshots/](../../../docs/design/screenshots/)** (raiz, sem `lovable-reference/`) — prints das telas já implementadas no app real, por task (`scrum-XX-*.png`). Útil para ver o que já foi adaptado e como.

Se a tela que você vai construir não tem print de referência ainda: clone o repo do Lovable, rode (`npm install && npm run dev`), navegue até a rota equivalente e **capture o print antes de implementar** — não implemente de memória ou suposição. Depois de capturar, salve em `docs/design/screenshots/lovable-reference/` e referencie no mapeamento.

## Regra de divergência

A única razão legítima pra uma tela divergir do print de referência é **campo/seção que não existe no domínio real** (schema do backend implementado até a fase atual, ou regra de negócio que ainda não existe). Nesses casos:
- Adapte (não invente dado falso pra preencher um campo do Lovable que não existe no domínio).
- **Documente a adaptação em `lovable-mapeamento.md`**, na seção da tela correspondente — outro dev (ou você mesmo depois) precisa entender que a diferença é intencional, não descuido.

Divergir só porque "ficou mais simples de implementar", porque não deu tempo de olhar a referência, ou por gosto pessoal **não é motivo válido**.

Exemplos já registrados (ver mapeamento para o texto completo): grid de specs do lote (2 cards, não 3 — sem `frente`/`fundo` no domínio), cadastro de cliente (1 campo de contato, não 2 + seletor de origem — sem esses campos no `Cliente` do backend), sem "Reserva válida até" (sem prazo de reserva no MVP).

## Padrões recorrentes (não redescrever a cada tela — usar os componentes/estilos já prontos)

- **`shared.cardSurface`** (`mobile/src/theme/shared.ts`): cards com fundo branco, borda, raio grande, sombra leve.
- **`shared.stickyFooter`**: barra fixa no rodapé que **substitui** o `BottomNav` (nunca os dois juntos) — usada em qualquer tela com uma ação principal (detalhe do lote, formulário com botão de salvar). Ver `MobileShell` do repo de referência: `footer` presente ⇒ nav escondido.
- **`Field`** (`mobile/src/components/Field.tsx`): label em texto normal **acima** do input (não label flutuante), placeholder de exemplo, hint opcional abaixo em `mutedForeground`. Usar em todo formulário novo.
- **`StatusBadge`**: cor + texto + `dot`, nunca só cor (acessibilidade).
- **`BottomNav`**: item sem tela ainda fica visível só com `enabled: false` — nunca um `href` morto, nunca escondido (fidelidade visual com o repo de referência, que sempre mostra os 4 itens).

## Do skill de design da Anthropic (`frontend-design`) — o que se aplica aqui

O skill original é sobre *criar* uma identidade visual do zero; aqui a identidade já está fechada (Lovable + mapeamento). Mesmo assim, alguns princípios são transferíveis:

- **Autocrítica com screenshot antes de considerar a tela pronta.** Não é opcional — suba a tela (`expo start --web` serve só pra captura, mesmo sendo app nativo) e tire o print antes de dizer que terminou. Uma tela nunca vista rodando é a causa mais comum de divergência silenciosa do que foi planejado.
- **Um único momento de destaque por tela, o resto quieto e disciplinado.** No LotIAdo isso já é a cor `primary` (terracota) reservada pra ação principal e valores em destaque — não espalhe `primary` em vários elementos da mesma tela competindo por atenção.
- **Evite os tiques de "design genérico"**: rótulo em CAIXA ALTA sem necessidade, destacar uma palavra isolada num título com cor/itálico, labels tipográficos redundantes só decorando (ex.: um "eyebrow" acima de todo card sem função). O padrão do LotIAdo já evita isso (labels em `mutedForeground`, sentence case) — não reintroduza.
- **Marcadores numerados (01/02/03) só quando o conteúdo é de fato uma sequência** (ex.: um wizard de passos). Não usar como decoração.
- **Movimento (animação) só quando responde a uma ação do usuário ou é um único momento orquestrado** (ex.: o fade+scale do `SplashAnimation` na abertura do app é o único "momento" intencional hoje) — não adicionar fade-in em cada card ou transição solta "porque fica bonito".
- **Copy é conteúdo de design, não decoração.** Nomeie do ponto de vista de quem usa (ex.: "Reservar", não "Executar reserva"), voz ativa, o mesmo verbo do botão até a confirmação (`Reservar` → depois `Reservado`, não um texto de sucesso com verbo diferente). Erros de negócio (409/422) explicam o que aconteceu na voz da interface, sem pedir desculpa e sem jargão de sistema (ex.: "Lote já reservado por outro corretor", não "Conflict: resource state invalid").
- **Piso de qualidade não-negociável**: funciona em largura de tela de celular, foco de teclado visível em campos, paleta de status sempre cor+texto (já é regra própria daqui).

## Processo pra tela nova

1. Achar a task no backlog → ver se ela referencia uma tela do Lovable.
2. Abrir o print equivalente em `docs/design/screenshots/lovable-reference/` (ou capturar um novo, ver acima).
3. Conferir contra o domínio real (`docs/01-analise-requisitos.md`, modelos do backend) o que existe e o que não existe — decidir adaptações **antes** de codificar.
4. Implementar usando os componentes/estilos já mapeados (não estilizar no improviso).
5. Subir a tela de verdade e tirar print — comparar lado a lado com a referência.
6. Se algo divergiu por motivo de domínio, atualizar `lovable-mapeamento.md` na mesma tarefa.
7. Print final vai no PR (`/create-pr` já cobra isso).
