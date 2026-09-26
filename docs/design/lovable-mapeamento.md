# Mapeamento — Identidade Visual Gerada no Lovable

Referência: [talles-coder/lotiado-gest-o-imobili-ria-inteligente](https://github.com/talles-coder/lotiado-gest-o-imobili-ria-inteligente) (gerado no Lovable a partir de [lovable-brief.md](lovable-brief.md)).

**Esta é a identidade visual adotada** — não é mais proposta em aberto. Qualquer tela nova (mobile ou backoffice web) segue os tokens e padrões deste documento. O repo do Lovable é só referência de estilo (React/Vite/Tailwind) — o código não é reaproveitado, só o que está mapeado aqui.

**Prints de todas as telas do repo de referência (login, home, lista/detalhe de loteamento, os 5 status de lote, cadastro de cliente, backoffice) ficam em [`screenshots/lovable-reference/`](screenshots/lovable-reference/)** — capturados direto do app Lovable rodando (`npm run dev`), não são mockups. Antes de implementar ou revisar qualquer tela nova (mobile ou backoffice web), **olhe o print da tela equivalente ali primeiro** — layout, hierarquia, espaçamento e qual elemento é fixo (header/footer) vs. rolável. Ausência de um campo/seção no domínio real (Fase 1) é motivo pra adaptar (nunca inventar dado só pra bater com o print — ver correções abaixo), mas divergência de **estilo/estrutura** sem motivo de domínio não é.

## Tipografia

- **Display (títulos, valores em destaque, logo):** `Outfit`, peso 500–700.
- **Corpo (texto, labels, inputs):** `Figtree`, peso 400–700.
- Ambas via Google Fonts. No app real: `@expo-google-fonts/outfit` + `@expo-google-fonts/figtree`.
- `letter-spacing: -0.01em` nos títulos (levemente condensado).

## Cores (convertidas de `oklch()` pra hex — RN não entende oklch)

Paleta "terra quente" — cream/terracota/verde, nada de azul-corporativo genérico. `primary` é o token trocável por tenant (branding customizável, ver `01-analise-requisitos.md` seção 3); o resto da paleta precisa continuar funcionando com outro `primary`.

| Token | Hex | Uso |
|---|---|---|
| `background` | `#FDFAF4` | fundo de tela (cream) |
| `foreground` | `#271D17` | texto principal |
| `card` | `#FFFFFF` | fundo de card |
| `primary` | `#DB551D` | terracota — ação principal, links, valores em destaque. **Trocável por tenant.** |
| `primary-foreground` | `#FEFBF8` | texto sobre `primary` |
| `primary-soft` | `#FFE8DC` | fundo suave com `primary` (chips, hover) |
| `secondary` | `#F5EDE4` | fundo neutro secundário (chips de característica) |
| `secondary-foreground` | `#3A2A20` | texto sobre `secondary` |
| `muted` | `#F5EFE7` | fundo apagado (barras de progresso, inputs disabled) |
| `muted-foreground` | `#6F6056` | texto secundário/legendas |
| `accent` | `#25984D` | verde folha — CTA alternativo, destaque de IA |
| `accent-foreground` | `#FEFBF8` | texto sobre `accent` |
| `accent-soft` | `#DAF8DF` | fundo suave com `accent` |
| `earth` | `#442C22` | marrom-argila escuro — blocos sólidos (topo do login, banner de IA) |
| `earth-foreground` | `#F9F4EE` | texto sobre `earth` |
| `destructive` | `#D73337` | ações destrutivas (cancelar) |
| `border` / `input` | `#E4DDD3` / `#DDD6CD` | bordas |

### Paleta de status (cor + texto, nunca só cor — acessibilidade)

| Status | Cor | Hex | Fundo suave |
|---|---|---|---|
| Disponível | verde | `#007F35` | `#D8F9DD` |
| Reservado | âmbar | `#B76C00` | `#FFF0C5` |
| Vendido | azul | `#2A669F` | `#DDEDFF` |
| Indisponível | vermelho | `#C92F33` | `#FFE6E3` |

Nota de design: "vendido" usa **azul**, não cinza — é um estado concluído/positivo, não neutro.

⚠️ **Correção em relação ao repo de referência do Lovable:** lá o domínio tinha 5 status (`disponível/reservado/vendido/bloqueado/inativo`). O enum real implementado no backend (`LoteStatus`, `backend/app/loteamentos_lotes/domain/state_machine.py`, FASE1-IMPL-01) tem só **4**: `disponivel/reservado/vendido/indisponivel`. `indisponivel` herda a cor de "bloqueado" (vermelho) — é um estado administrativo que só retorna a `disponivel`, mais próximo de um bloqueio do que de um arquivamento neutro. Não existe "inativo" como status de lote nesta versão do domínio — não usar esse token.

## Forma, raio e sombra

- Raio base `0.75rem` (12px): botões e inputs. Cards usam raio maior (`1rem`/16px). Badges/pills são `rounded-full`.
- Botões e inputs têm altura mínima generosa (**52px**) — alvo de toque grande, pensado pra uso em campo.
- Sombra sutil com tom quente (nunca cinza puro): cards com sombra leve; barra de ação fixa no rodapé com sombra "flutuante" mais forte pra separar do conteúdo.

## Ícones

Biblioteca `lucide` (o repo web usa `lucide-react`). No app: `lucide-react-native` (mesmo desenho de ícone, mesma API de props `size`/`color`) — não usar emoji nem misturar com outro set de ícone.

## Componentes mapeados

- **Logo**: marca quadrada com cantos arredondados, preenchida com `primary`, com uma cruz dividindo em 4 (referência visual a "terreno dividido em lotes") e um quadrado menor no canto preenchido com `accent`. Ao lado, o wordmark: `Lot` + `IA` (cor `primary`, com uma barrinha `accent` sublinhando) + `do`. Fonte display, peso bold.
- **StatusBadge**: pill (`rounded-full`) com fundo "soft" da cor do status + texto na cor forte do status + um pontinho (`dot`) da cor forte antes do texto. Sempre cor + texto, nunca só cor.
- **Cards** (`card-surface`): fundo branco, borda 1px `border`, raio grande, sombra leve.
- **Botões**: 4 variantes — `primary` (fundo `primary`), `accent` (fundo `accent`, usado pra ação relacionada a IA/conversão), `outline` (contorno, fundo `card`), `danger` (contorno vermelho, usado só em ações destrutivas tipo cancelar reserva).
- **Barra de ação fixa no rodapé**: muda de conteúdo conforme o status do lote (ver `lotes.$id.tsx` no repo, adaptado aos 4 status reais — ver nota acima) — disponível → botão "Reservar"; reservado → "Cancelar reserva" (danger) + "Converter em venda" (accent); vendido/indisponível → faixa informativa sem ação, na cor "soft" do status. **Ela substitui o `BottomNav`, nunca aparece junto** (mesma regra do `footer` vs. nav do `MobileShell` no repo) — só a tela sem nenhuma ação disponível (ex.: lista de lotes) mostra o `BottomNav`.
- **Campo de formulário (`Field`)**: label em texto normal **acima** do input (não label flutuante dentro do campo) + input com placeholder de exemplo + hint opcional abaixo em `muted-foreground` (ver `Field` em `clientes.novo.tsx` no repo e `src/components/Field.tsx` no app). Usado em qualquer formulário novo — cadastro de cliente é o primeiro caso (SCRUM-65).

## Padrões de tela mapeados

- **Login**: bloco superior sólido na cor `earth` (com um padrão sutil de grade em SVG, ~15% opacidade — reforça a metáfora de "terreno em grade/lotes"), logo grande + tagline dentro desse bloco; formulário abaixo em fundo `background` (cream).
- **Home**: saudação personalizada (nome vindo de `GET /auth/me`), 3 cards de indicador lado a lado, banner de entrada pro assistente de IA (fundo `earth`, ícone em bolha `accent`, texto de exemplo de pergunta) e lista de "loteamentos recentes" (cards com contagem de disponíveis). Duas adaptações em relação ao repo original, por falta de dado real no domínio da Fase 1: os indicadores são **Disponíveis/Reservados/Vendidos totais** (não "reservas ativas"/"vendas no mês" — não há timestamp de transição de status pra filtrar por período, então rotular como "no mês" seria inventar dado); e não existe seção de "reservas vencendo" (não há campo de prazo de reserva no domínio — reserva não expira no MVP, ver `01-analise-requisitos.md`). O banner de IA fica visível mas sem ação (RAG/agente é Fase 7+) — chega a "Em breve", nunca a um link morto.
- **Lista de loteamentos**: busca no topo, cards com nome/cidade, número disponível (destacado na cor `status.disponivel`) + barra de progresso percentual.
- **Lista de lotes de um loteamento**: chips de filtro por status (Todos/Disponíveis/Reservados/Vendidos/Indisponíveis) roláveis horizontalmente; cada card tem uma faixa colorida grossa na borda esquerda (**6px**, cor forte do status — não 4px, fica fina/errada) além do `StatusBadge` à direita; a área fica em cinza (`muted-foreground`) mas o **preço é `bodySemiBold` + `foreground`**, não cinza — só a área é secundária, o preço é informação primária.
- **Detalhe do lote**: cabeçalho com identificação + `StatusBadge`; card de preço em destaque; grid de specs; chips de características; seção de cliente (quando reservado/vendido); placeholder de localização na planta; botão "Cadastrar novo cliente" (outline, sempre visível, independente do status); barra de ação fixa no rodapé (ver componentes acima). **Adaptação em relação ao repo**: o grid de specs lá tem 3 cards (área/frente/fundo) — o domínio real (Fase 1) não tem frente/fundo como campos do lote, só `area_m2` e `quadra`, então o grid daqui tem 2 cards (área/quadra) em vez de inventar frente/fundo. Pelo mesmo motivo, não existe a linha "Reserva válida até" (sem campo de prazo de reserva no domínio, ver nota da Home) nem o "ou 120x de R$X" no card de preço (sem modelo de parcelamento na Fase 1).
- **Cadastro de cliente**: formulário com `Field` (nome completo, CPF/CNPJ, contato) — layout e placeholders seguem o repo de referência. **Adaptação**: o repo tem "WhatsApp" e "E-mail (opcional)" como dois campos, mais um seletor "Como conheceu o loteamento?" (chips). O domínio real (`Cliente`, Fase 1) só tem um campo `contato` (string única) e não tem origem/canal de aquisição — então aqui é **um** campo "Contato" (com o hint "Usaremos para enviar a proposta.", igual ao repo) e sem o seletor de origem. Não adicionar esses campos/seções de volta sem que o domínio ganhe suporte pra eles primeiro (mudança de schema é decisão de arquitetura, não de UI).
- **Abertura do app**: splash nativo é só fundo sólido `background` (sem imagem — não há asset raster do logo ainda); assim que o JS sobe, o `Logo` aparece com fade + scale-in, segura ~450ms, e dá fade-out revelando a tela real (padrão tipo iFood/Nubank). Ver `src/components/SplashAnimation.tsx`.
- **Navegação mobile**: bottom nav de 4 itens (Início / Loteamentos / Cliente / Backoffice) — ícone em pill `primary-soft` quando ativo, cor `primary` no texto/ícone ativo, `muted-foreground` inativo. "Backoffice" (Fase 5) ainda não tem tela: fica visível (fidelidade visual) mas `disabled` — nunca um `href` morto. "Cliente" (SCRUM-65) já linka pro cadastro de cliente. Ver `src/components/BottomNav.tsx`. É substituída pela barra de ação fixa (nunca as duas juntas) nas telas que ganham uma ação principal — detalhe do lote (SCRUM-65: reservar/converter/cancelar) e formulário de cliente (salvar).
- **Corretores (lista/cadastro/edição) e Usuários (lista/convite)** (SCRUM-71): sem tela equivalente no repo de referência do Lovable (não existe rota `corretores`/`usuarios`/`equipe` lá — conferido clonando e listando `src/routes/`). Construídas reaproveitando os padrões já mapeados (não um estilo novo): lista com busca (igual Loteamentos), formulário com `Field` (igual Cadastro de cliente), cabeçalho com back + título + ação (igual Novo cliente), confirmação destrutiva via `Alert.alert` (igual cancelar reserva no detalhe do lote). Badge de papel (`role`) em pill `muted`; badge de status ativo/desativado segue o padrão cor+texto+dot dos status de lote (verde/`status.disponivel` para ativo, vermelho/`status.indisponivel` para desativado) — não é um novo token, é reuso semântico dos mesmos dois tons. Sem entrada na `BottomNav` (fixa em 4 itens por fidelidade ao repo de referência): acessadas por uma seção "Gestão" na Home, dois cards no mesmo estilo de "Loteamentos recentes". Prints em `screenshots/scrum-71-*.png`.
- **Mapa do loteamento** (SCRUM-70): sem tela equivalente no repo de referência do Lovable. Reaproveita o cabeçalho (back + título) da lista de lotes, aberto por um botão de ícone (`Map`) no cabeçalho dela. Polígonos usam `colors.status[...].text` (borda opaca + preenchimento com ~70% de opacidade); legenda em rodapé `card` com dot + texto por status (mesma regra "nunca só cor"). Sem cor nova.

## Regra permanente

**Todo trabalho de estilo/UI daqui pra frente (mobile ou backoffice web) segue os tokens e padrões deste documento** — não inventar cor, fonte, raio ou componente novo fora daqui. Se algo não estiver mapeado (uma tela nova, por exemplo), a extensão da paleta/padrões deve manter a mesma lógica (cream/terracota/verde, `earth` pra blocos sólidos, status sempre cor+texto+dot) em vez de introduzir um estilo novo. Mudança de direção visual passa por aqui primeiro (atualiza este arquivo), nunca só no código.
