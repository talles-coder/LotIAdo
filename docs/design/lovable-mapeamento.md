# Mapeamento — Identidade Visual Gerada no Lovable

Referência: [talles-coder/lotiado-gest-o-imobili-ria-inteligente](https://github.com/talles-coder/lotiado-gest-o-imobili-ria-inteligente) (gerado no Lovable a partir de [lovable-brief.md](lovable-brief.md)).

**Esta é a identidade visual adotada** — não é mais proposta em aberto. Qualquer tela nova (mobile ou backoffice web) segue os tokens e padrões deste documento. O repo do Lovable é só referência de estilo (React/Vite/Tailwind) — o código não é reaproveitado, só o que está mapeado aqui.

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
| Bloqueado | vermelho | `#C92F33` | `#FFE6E3` |
| Inativo | cinza | `#787069` | `#EFEAE5` |

Nota de design: "vendido" usa **azul**, não cinza — é um estado concluído/positivo, não neutro. "Inativo" fica cinza (neutro/arquivado). Isso é intencional e deve ser mantido — reforça visualmente que vender é bom, arquivar é neutro.

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
- **Barra de ação fixa no rodapé**: muda de conteúdo conforme o status do lote (ver `lotes.$id.tsx` no repo) — disponível → botão "Reservar"; reservado → "Cancelar reserva" (danger) + "Converter em venda" (accent); vendido/bloqueado/inativo → faixa informativa sem ação, na cor "soft" do status.

## Padrões de tela mapeados

- **Login**: bloco superior sólido na cor `earth` (com um padrão sutil de grade em SVG, ~15% opacidade — reforça a metáfora de "terreno em grade/lotes"), logo grande + tagline dentro desse bloco; formulário abaixo em fundo `background` (cream).
- **Home**: saudação personalizada, 3 cards de indicador lado a lado (disponíveis/reservas ativas/vendas no mês, cada um com a cor do status correspondente), banner de entrada pro assistente de IA (fundo `earth`, ícone em bolha `accent`, texto de exemplo de pergunta), lista de "loteamentos recentes" (cards com % de disponibilidade e barra de progresso), lista de "reservas vencendo".
- **Lista de loteamentos**: busca no topo, cards com nome/cidade, número disponível + barra de progresso percentual.
- **Detalhe do lote**: cabeçalho com identificação + `StatusBadge`; card de preço em destaque; grid de 3 specs (área/frente/fundo); chips de características; seção de cliente (quando reservado/vendido); placeholder de localização na planta; barra de ação fixa no rodapé (ver componentes acima).
- **Navegação mobile**: shell com largura máxima tipo cartão centralizado (`max-w-md`), header sticky com botão voltar + título, bottom nav sticky de 4 itens (Início / Loteamentos / Cliente / Backoffice) — substituída pela barra de ação fixa quando a tela tem uma ação principal (ex.: detalhe do lote).

## Regra permanente

**Todo trabalho de estilo/UI daqui pra frente (mobile ou backoffice web) segue os tokens e padrões deste documento** — não inventar cor, fonte, raio ou componente novo fora daqui. Se algo não estiver mapeado (uma tela nova, por exemplo), a extensão da paleta/padrões deve manter a mesma lógica (cream/terracota/verde, `earth` pra blocos sólidos, status sempre cor+texto+dot) em vez de introduzir um estilo novo. Mudança de direção visual passa por aqui primeiro (atualiza este arquivo), nunca só no código.
