# Brief para o Lovable — Identidade Visual do LotIAdo

> Copiar este documento (ou os trechos relevantes) direto no chat do Lovable. Objetivo: gerar **logo + identidade visual** (paleta, tipografia, mood das telas). O código React/Vite que o Lovable gerar **não** vai para produção — o app real é Expo/React Native (mobile) + Expo for Web (backoffice). O que aproveitamos daqui é a direção visual, depois portada manualmente pros tokens do design system real.

---

## 1. Produto

**Nome:** LotIAdo — trocadilho com "loteado" (ação de dividir um terreno em lotes) + "IA", porque o produto usa inteligência artificial (RAG + agentes) pra ajudar na gestão. O "IA" dentro do nome é uma característica central da marca, não um detalhe — vale a pena o logo/wordmark destacar essas duas letras de alguma forma (cor, peso, ou um pequeno elemento gráfico), sem virar piada visual boba.

**O que é:** SaaS multitenant para gestão de loteamentos, imóveis e negociações imobiliárias. Um app mobile (uso em campo por corretores) + um backoffice web (mesma base de código, telas administrativas) + IA (busca em documentos, agente de apoio).

**Não é:** um marketplace de busca de imóvel pra consumidor final (tipo QuintoAndar/ZAP) — é uma ferramenta de trabalho pra quem já vende loteamentos.

## 2. Quem usa

- **Corretor** (uso principal, em campo, pelo celular): consulta lotes disponíveis, cadastra cliente, reserva/vende um lote. Perfil variado de conforto com tecnologia — muitos não são "early adopters" de apps novos, usam o essencial (WhatsApp, Instagram, apps de banco). **Não é um público que se impressiona com visual "tech" ou futurista — pelo contrário, isso pode gerar desconfiança.**
- **Gestor/administrador** (backoffice web, no computador): visão geral do estoque de lotes, funil de vendas, cadastros.

## 3. Direção de estilo (o mais importante deste brief)

- **Minimalista, mas com alma.** Não é um app "vazio" tipo protótipo cinza — precisa ter personalidade e calor humano, só que sem poluição visual.
- **Nada de futurista/muito moderno.** Sem gradientes chamativos, glassmorphism, dark-mode-first, tipografia exótica ou paleta neon. Isso afasta o público-alvo (corretor de meia-idade, não um early adopter).
- **Familiar, não genérico.** Seguir os padrões de interação de apps brasileiros de sucesso que esse público já usa todo dia — cards, listas, botões grandes, hierarquia clara tipo Nubank (confiança, clareza) e iFood (cards de lista bem resolvidos) — mas a **paleta e o tom não podem parecer fintech nem delivery**. Precisa remeter a **terra, propriedade, construção civil** — algo mais terroso/caloroso do que o azul-corporativo padrão de SaaS.
- **Confiável antes de bonito.** É uma ferramenta que lida com reserva/venda de patrimônio real — o tom visual deve passar seriedade e solidez, não "startup descolada".
- **Acessível em campo:** contraste alto o suficiente pra ler sob luz de sol, tamanhos de toque grandes (é usado andando por um terreno, não sentado numa mesa).

**Adjetivos-guia:** confiável, direto, caloroso, sólido, sem jargão. **Evitar:** hype, frio, genérico-corporativo, infantil.

## 4. O que pedir pro Lovable gerar

1. **Logo/wordmark** do "LotIAdo", com tratamento visual pro "IA" dentro do nome.
2. **Paleta de cores**: 1 cor primária + 1 cor de destaque (accent) + neutros. Ver restrição técnica no item 6 — a cor primária precisa poder ser trocada por tenant no futuro, então o resto da identidade (tipografia, ícones, layout) não pode depender só dela pra "funcionar".
3. **Tipografia**: 1 fonte pra títulos + 1 pra corpo de texto (pode ser a mesma família em pesos diferentes). Evitar fontes "tech" (nada de mono, nada excessivamente geométrico/futurista).
4. **Paleta de status com cor + texto** (não só cor, por acessibilidade): `Disponível`, `Reservado`, `Vendido`, `Bloqueado`, `Inativo` — precisam ser visualmente distintos e o significado (positivo/neutro/negativo) precisa ficar óbvio à primeira vista.
5. **Mockups de referência** (opcional, mas ajuda a validar o mood) nas telas do item 5 abaixo.

## 5. Telas/fluxos reais do produto (pra não gerar conteúdo genérico)

- **Login** — e-mail + senha.
- **Home** — visão geral rápida (ex.: loteamentos recentes, indicadores simples).
- **Lista de Loteamentos** — cards com nome, cidade, quantidade de lotes disponíveis vs. total.
- **Lista de Lotes de um loteamento** — cada lote tem: identificação, quadra, área (m²), preço, status (ver item 4). Puxado com frequência em campo, então precisa escanear rápido.
- **Detalhe do Lote** — specs completas (área, quadra, preço, características) + ação principal fixa (Reservar / Converter em venda / Cancelar reserva — a ação disponível muda de acordo com o status atual do lote).
- **Cadastro de Cliente** — formulário simples (nome, documento, contato).
- **Backoffice web (versão desktop)** — mesmas telas de domínio + funil de vendas (reservas → vendas) em visão mais densa, tipo kanban ou tabela — não é um produto visual separado, é uma extensão mais "cheia" do mesmo app.

## 6. Restrições técnicas (importante pro Lovable saber, mesmo não sendo quem implementa)

- O app real roda em **React Native + Expo** (mobile) e a mesma base compilada pra **web** (Expo for Web) — o código do Lovable é só referência visual, não vai ser reaproveitado como está.
- A cor primária/logo do LotIAdo pode um dia ser **trocada por tenant** (white-label parcial) — então a identidade não pode depender de um azul ou verde específico pra "fazer sentido"; o sistema de cor precisa se sustentar com outra cor primária no lugar, se necessário.
- Biblioteca de componentes do app real é **React Native Paper** (Material Design 3) — não é obrigatório o Lovable seguir Material, mas ajuda se os componentes gerados (botões, cards, inputs) tiverem formas/tamanhos fáceis de traduzir pra componentes Material depois (raio de borda, altura de botão, etc. — nada arredondado demais tipo iOS nem quadrado demais tipo enterprise antigo).

---

*Depois do Lovable gerar a direção, o resultado (paleta + tipografia + logo) vira a base de `docs/design/proposta-design-system.md` (D9) e só então é portado pro código do app (`mobile/`).*
