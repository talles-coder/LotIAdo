# Fase 3 — Mobile MVP

Entrega desta fase: app React Native (Expo) funcional consumindo a API real — login, listagem/detalhe de loteamentos e lotes, cadastro de clientes, criar reserva/venda. Sem mapa (isso é Fase 4) e sem cache offline (isso é Fase 6) — objetivo é validar a pilha mobile isoladamente.

## Épico E3.1 — Setup do projeto mobile

### FASE3-EST-01-D1 / FASE3-EST-01-D2 — Estudo: Expo + React Native + navegação
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** montar e rodar um projeto Expo/TypeScript com navegação entre telas e chamadas HTTP autenticadas.
- **Conceitos a entender:** Expo Router (ou React Navigation) para pilha de telas; gerenciamento de estado de autenticação (token JWT em `expo-secure-store`); cliente HTTP com interceptor de token (axios ou `fetch` + wrapper); gerenciamento de estado de servidor (TanStack Query) para cache/loading/erro de requisições.
- **Material recomendado:** documentação oficial do Expo (Expo Router); documentação do TanStack Query para React Native.
- **Exercício prático:** criar um app Expo isolado com duas telas (lista → detalhe) consumindo uma API pública qualquer, com estado de loading/erro tratado via TanStack Query.
- **Critério de conclusão:** exercício navega entre telas e trata estado de loading/erro sem lógica duplicada em cada tela.
- **Paralelizável:** Sim.

### FASE3-IMPL-01 — Setup do projeto Expo + autenticação
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** app inicializa, permite login e mantém sessão.
- **Descrição:** criar projeto Expo/TypeScript; tela de login consumindo `POST /auth/login` (Fase 0); armazenar token através de um módulo `storage` próprio (não chamar `expo-secure-store` diretamente nas telas) — hoje com uma única implementação nativa, mas já isolado atrás de uma interface simples (`getToken`/`setToken`/`clearToken`) para receber, sem retrabalho, uma implementação `.web.tsx` (usando `localStorage`) quando o Expo for Web entrar na Fase 5 (decisão D2 em [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md)); interceptor HTTP que anexa o token e trata 401 (redireciona para login).
- **Pré-requisitos:** FASE3-EST-01-D2.
- **Dependências:** FASE0-IMPL-05 (endpoint de login já existe).
- **Resultado esperado:** login funcional no app, sessão persiste entre reaberturas do app.
- **Critérios de aceite:** login com credenciais válidas navega para a home; logout limpa o token; 401 em qualquer chamada redireciona para login.
- **Paralelizável:** Sim, com FASE3-IMPL-02 (que pode ser desenvolvida contra dados mockados até o login estar pronto).
- **Conhecimentos novos introduzidos:** armazenamento seguro de token, interceptor HTTP.

## Épico E3.2 — Telas de domínio

### FASE3-IMPL-02 — Listagem e detalhe de loteamentos/lotes
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** corretor/gestor consegue navegar loteamentos → lotes → detalhe do lote.
- **Descrição:** tela de lista de loteamentos; tela de lista de lotes de um loteamento (com status visível); tela de detalhe do lote (todas as informações do domínio da Fase 1).
- **Pré-requisitos:** FASE3-EST-01-D1.
- **Dependências:** FASE1-IMPL-01 (endpoints já existem); integra com FASE3-IMPL-01 para autenticação.
- **Resultado esperado:** três telas navegáveis com dados reais da API.
- **Critérios de aceite:** lista/detalhe refletem o estado atual do lote (inclusive após uma transição feita via API/Swagger, ao dar pull-to-refresh).
- **Paralelizável:** Sim, com FASE3-IMPL-01 (pode mockar auth no início).
- **Conhecimentos novos introduzidos:** nenhum além de FASE3-EST-01.

### FASE3-IMPL-03 — Cadastro de clientes e criação de reserva/venda
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** corretor consegue, pelo app, cadastrar um cliente e reservar/vender um lote.
- **Descrição:** formulário de cliente; ação "reservar" na tela de detalhe do lote (chama `POST /reservas`); ação "converter em venda" e "cancelar reserva" quando aplicável ao status atual.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE3-IMPL-02, FASE1-IMPL-02, FASE1-IMPL-03.
- **Resultado esperado:** fluxo completo reserva → venda executável pelo app.
- **Critérios de aceite:** ações de reserva/venda só aparecem habilitadas quando o status do lote permite (espelhando a tabela de transições da Fase 1); erro do backend (ex.: lote já reservado por outro corretor entretanto) é exibido de forma clara ao usuário.
- **Paralelizável:** Não pode ser finalizada antes de FASE3-IMPL-02 (tela de detalhe) existir, mas o formulário de cliente pode ser desenvolvido em paralelo.
- **Conhecimentos novos introduzidos:** tratamento de erro de negócio vindo da API (409/422) na UI.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE3-EST-01 → FASE3-IMPL-02 (listagem/detalhe).
- **Dev 2:** FASE3-EST-01 → FASE3-IMPL-01 (setup/auth) → FASE3-IMPL-03 (clientes/reserva/venda).
- **Pontos de sincronização:**
  1. Contrato de resposta dos endpoints de loteamento/lote (formato JSON, nomes de campo) já está fixado desde a Fase 1 (OpenAPI gerado pelo FastAPI) — usar o `/docs` como fonte de verdade evita divergência entre mobile e backend.
  2. FASE3-IMPL-03 depende da tela de detalhe (FASE3-IMPL-02) existir para adicionar as ações — combinar a interface do componente de detalhe antes.
- Esta fase pode ocorrer **em paralelo com a Fase 4 (GIS)** no backend, já que ambas partem da Fase 2 concluída e não têm dependência direta entre si — ver observação em [04-roadmap.md](../04-roadmap.md).
