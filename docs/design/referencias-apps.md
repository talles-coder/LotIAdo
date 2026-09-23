# Referências de Design — Apps do Nicho Imobiliário

Pesquisa de apoio para SCRUM-63 (comentário: "adicionalmente definir o design da aplicação"). Objetivo: reunir referências de apps/produtos consolidados que resolvem problemas parecidos com os do LotIAdo — para termos um vocabulário visual e de interação comum antes de desenhar as telas da Fase 3 (mobile) e Fase 5 (backoffice web).

LotIAdo tem duas superfícies com necessidades diferentes, então as referências estão separadas por superfície:

- **Mobile (corretor em campo):** listagem/detalhe de lote, reserva/venda rápida — precisa de velocidade e clareza em uma tela pequena.
- **Web backoffice (gestor):** visão geral de estoque de lotes, funil de vendas, auditoria — precisa de densidade de informação sem virar bagunça.

## 1. Apps mobile de listagem imobiliária (referência de UI de listagem/detalhe)

### QuintoAndar
- Tela de exploração: busca + switch aluguel/compra + filtros rápidos + feed de cards de imóvel.
- Tela de detalhe: carrossel de fotos no topo, composição de custo **discriminada** (não só um número final), especificações e amenidades em lista, **barra de ação fixa no rodapé** ("Agendar visita" / "Fazer proposta") que segue o scroll.
- Favoritos com estado vazio ilustrado (empty state), não só texto genérico.
- **O que mirar no LotIAdo:** a barra de ação fixa no rodapé da tela de detalhe do lote (ex.: "Reservar" / "Converter em venda") é diretamente aplicável — em vez de um botão perdido no fim de uma tela longa de especificações do lote.

### ZAP Imóveis (design system próprio, tokenizado)
- Paleta com papéis semânticos claros (`primary`, `primaryDark`, `primaryLight` etc.), não cores soltas por tela.
- **O que mirar no LotIAdo:** vale a pena definir tokens semânticos (não hexadecimais direto no componente) desde a Fase 3, mesmo que o design system em si seja simples — isso é o que evita retrabalho quando o Expo for Web entrar na Fase 5 (D2/D8 em `03-decisoes-tecnicas.md`).

### Padrões gerais de 2026 para apps de listagem imobiliária (LuxuryPresence, DesignRush, Mobbin — ver fontes)
- Hierarquia de conteúdo: preço, área e localização **antes** de texto longo — o card não deve enterrar o dado que decide a ação.
- CTAs sempre "ao alcance do polegar" (thumb reach) — botões de ação primária na parte inferior da tela, não no topo.
- Badges de status com cor + texto (nunca só cor) — importante para acessibilidade e é exatamente o padrão que o LotIAdo precisa para status do lote (`disponível` / `reservado` / `vendido`).

**Fontes:**
- [QuintoAndar Design (Medium)](https://medium.com/quintoandar-design)
- [Real Estate Website UI/UX Design: The 2026 Guide](https://www.luxurypresence.com/blogs/real-estate-website-user-interface-ui-ux/)
- [Best Real Estate App Designs of 2026 — DesignRush](https://www.designrush.com/best-designs/apps/real-estate)
- [Real Estate App Design UI Examples — Mobbin](https://mobbin.com/explore/mobile/app-categories/real-estate)

## 2. Software de gestão de loteamentos (referência direta de domínio)

Estas são as referências mais próximas do que o LotIAdo faz de fato — sistemas B2B para loteadoras/incorporadoras, não apps de busca de imóvel para consumidor final.

### CV CRM (Sienge) — líder de mercado em CRM imobiliário/loteamento no Brasil
- **Mapa de disponibilidade em tempo real**: mostra quais lotes estão reservados, disponíveis ou vendidos — visualização espacial do estoque, não só uma lista.
- **Portal do corretor** separado do painel do gestor: cada perfil vê só o que precisa (corretor não vê métricas gerenciais de toda a carteira).
- **O que mirar no LotIAdo:** confirma que o mapa de status de lotes (Fase 4 — GIS) é o componente central do produto, não um extra — a UI deveria ser desenhada em volta dele desde já, mesmo antes do GIS existir (ex.: a lista de lotes da Fase 3 já pode ter os mesmos badges de status que o mapa vai usar depois).

### Verde SL — sistema para loteamento (vendas, contratos, CRM, cobrança)
- Foco em todo o ciclo: da reserva ao contrato e cobrança — reforça que o fluxo reserva → venda do LotIAdo (FASE3-IMPL-03) é o núcleo do produto, não uma tela secundária.

**Fontes:**
- [CV CRM — Sienge](https://store.sienge.com.br/products/cv-crm)
- [CRM na gestão de vendas de lotes — CV CRM](https://cvcrm.com.br/blog/crm-na-gestao-de-vendas-de-lotes/)
- [CV CRM para empresa loteadora](https://cvcrm.com.br/blog/cv-crm-para-empresa-loteadora/)
- [Verde SL — Sistema para loteamento](https://verdesl.com.br/)

## 3. SaaS backoffice / CRM web (referência para o backoffice da Fase 5)

### Pipedrive (pipeline de vendas em kanban)
- Board kanban por estágio do funil, com drag-and-drop entre estágios.
- Cada card mostra só o essencial + indicador de status/urgência; deals que precisam de atenção sobem para o topo da coluna.
- **O que mirar no LotIAdo:** um board kanban por status de reserva/venda (Reservado → Em contrato → Vendido) é um padrão natural para a visão do gestor no backoffice web, reaproveitando os mesmos dados que já alimentam a lista mobile.

### Linear / Notion (referência de padrão geral, não específica do nicho)
- Densidade de informação alta mas organizada: sidebar de navegação fixa + área de conteúdo com tabelas/listas compactas.
- Estados vazios, loading e erro tratados como parte do design, não como afterthought — alinhado ao que a task FASE3-EST-01-D2 já pede ("sem lógica duplicada em cada tela").

**Fontes:**
- [Pipedrive — Sales Pipeline Management](https://www.pipedrive.com/en/features/pipeline-management)
- [Pipeline view: manage deals lifecycle — Pipedrive](https://support.pipedrive.com/en/article/pipeline-view)
- [SaaS UI — Real Interface Design Screenshots](https://www.saasui.design/)

## 4. Bibliotecas de componentes para Expo (mobile + web no mesmo código)

Pesquisa complementar, já que D2 (`03-decisoes-tecnicas.md`) define que mobile e web backoffice compartilham o mesmo código Expo — a biblioteca de componentes precisa funcionar nas duas plataformas.

| Biblioteca | Resumo | Observação para o LotIAdo |
|---|---|---|
| **React Native Paper** | Material Design 3, mantida pela Callstack, acessibilidade cuidada (alvos de toque 48×48dp, screen reader) por padrão. | Mais madura e simples de adotar; boa entrada para times pequenos. Web via React Native Web funciona mas não é o caso de uso mais testado da lib. |
| **Tamagui** | Sistema de tokens + compilador, pensado para apps universais (nativo + web) desde a raiz. | Setup mais pesado (arquivo de config, compilador); maior retorno justamente quando web é alvo de primeira classe — o que é o caso do LotIAdo a partir da Fase 5. |
| **Gluestack UI** | Construída sobre `@react-native-aria`; foco forte em acessibilidade de componentes complexos (modais, accordions) com focus trap. | Vale considerar se o backoffice tiver bastante modal/dropdown complexo. |

**Fontes:**
- [The 10 best React Native UI libraries of 2026 — LogRocket](https://blog.logrocket.com/best-react-native-ui-component-libraries/)
- [Best React Native UI libraries in 2026: an honest map](https://motionary.dev/blog/best-react-native-ui-libraries-2026)

## Síntese — o que puxar para o padrão do LotIAdo

1. **Badges de status (cor + texto)** para `disponível/reservado/vendido` — usados de forma idêntica na lista mobile (Fase 3), no mapa (Fase 4) e no kanban do backoffice (Fase 5). Definir esse componente uma vez, cedo.
2. **Barra de ação fixa no rodapé** na tela de detalhe do lote (mobile), com as ações válidas para o status atual (reservar/converter/cancelar — espelha a tabela de transição da Fase 1).
3. **Tokens semânticos de cor/espaçamento** desde a Fase 3, não cores soltas por tela — facilita a divergência mobile/web que D2 já antecipa.
4. **Visão kanban por estágio de venda** como padrão de referência para o backoffice web (Fase 5), reaproveitando os mesmos dados/status do mobile.
5. Biblioteca de componentes: **React Native Paper** (D9, decidido — ver [proposta-design-system.md](proposta-design-system.md) e [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md)).
