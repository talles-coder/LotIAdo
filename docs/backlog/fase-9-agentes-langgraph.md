# Fase 9 — Agentes com LangGraph

Entrega desta fase: agente conversacional que responde perguntas em linguagem natural sobre os dados do sistema usando tools reais (não apenas conhecimento do LLM), com confirmação humana antes de ações sensíveis.

## Épico E9.1 — Fundamentos de LangGraph

### FASE9-EST-01-D1 / FASE9-EST-01-D2 — Estudo: LangGraph — grafos de agente, tools e estado
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como modelar um agente como um grafo de estados com LangGraph, incluindo tool calling, branches condicionais e um ponto de pausa para confirmação humana.
- **Conceitos a entender:** `StateGraph` (nós, arestas, estado compartilhado); nó de decisão (o LLM escolhe qual tool chamar, com base em tool calling do modelo); arestas condicionais (branch conforme o resultado de um nó); ciclos (o agente pode voltar a um nó anterior, ex. pedir mais informação); "human-in-the-loop" — como pausar o grafo em um nó de confirmação e retomar após aprovação humana; tratamento de erro de uma tool (o grafo precisa lidar com falha sem travar).
- **Material recomendado:** documentação oficial do LangGraph (conceitos: StateGraph, tools, human-in-the-loop/interrupts).
- **Exercício prático:** construir um agente de brinquedo com 2 tools fictícias (ex.: "somar" e "buscar em uma lista fixa"), um nó de decisão que escolhe a tool certa, e um nó de confirmação humana antes de uma das tools (simulando uma ação "sensível").
- **Critério de conclusão:** o agente de brinquedo escolhe a tool correta para perguntas diferentes e pausa corretamente esperando confirmação antes da tool sensível.
- **Paralelizável:** Sim.

## Épico E9.2 — Tools do agente sobre os serviços existentes

### FASE9-IMPL-01 — Tools de consulta (lotes, disponibilidade, geo, clientes, corretores, vendas, condições comerciais)
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** o agente tem acesso a tools determinísticas que espelham exatamente os serviços de aplicação já existentes — nunca gera SQL nem "inventa" dados.
- **Descrição:** cada tool é uma função fina que chama um serviço de aplicação já existente (`LoteService`, `GeoQueryService` da Fase 4, `ClienteService`, `CorretorService`, `VendaService`) e formata o resultado para o LLM; declaração de schema de entrada de cada tool (Pydantic) para permitir tool calling estruturado; tool de busca de documentos reaproveita `POST /rag/buscar` (Fase 7).
- **Pré-requisitos:** FASE9-EST-01-D1.
- **Dependências:** FASE4-IMPL-02, FASE7-IMPL-03, FASE1 (todos os serviços de domínio).
- **Resultado esperado:** conjunto de tools testável isoladamente (fora do grafo do agente).
- **Critérios de aceite:** cada tool tem um teste unitário chamando-a diretamente com parâmetros de exemplo e validando o formato de saída.
- **Paralelizável:** Sim, com FASE9-IMPL-02 (o grafo pode ser desenvolvido com tools mockadas em paralelo).
- **Conhecimentos novos introduzidos:** design de tools para agente (schema de entrada, formatação de saída para LLM).

### FASE9-IMPL-02 — Grafo do agente: decisão, tool calling, resposta
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** o agente recebe uma pergunta em linguagem natural, decide qual(is) tool(s) usar, executa, e formata a resposta final.
- **Descrição:** `StateGraph` com nó de decisão (LLM com tool calling via `LLMProvider`), nó(s) de execução de tool, nó de formatação de resposta final; tratamento de erro de tool (ex.: tool retorna vazio → o agente informa que não encontrou resultado, não inventa).
- **Pré-requisitos:** FASE9-EST-01-D2.
- **Dependências:** FASE9-IMPL-01 (ou tools mockadas até estarem prontas).
- **Resultado esperado:** endpoint `POST /agente/perguntar` funcional para perguntas como as citadas no briefing ("lotes disponíveis > 200m² em esquina", "lotes até R$250 mil próximos da área verde").
- **Critérios de aceite:** as duas perguntas de exemplo do briefing retornam resultado correto usando as tools de FASE9-IMPL-01 (validado contra dados de teste conhecidos).
- **Paralelizável:** Sim, com FASE9-IMPL-01 (integração final depende das duas, mas o desenvolvimento pode ser paralelo com um contrato de tool combinado antes).
- **Conhecimentos novos introduzidos:** orquestração de agente com LangGraph, tool calling real com um modelo local via Ollama.

## Épico E9.3 — Confirmação humana para ações sensíveis

### FASE9-IMPL-03 — Nó de confirmação humana antes de ações destrutivas/sensíveis
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** o agente nunca executa uma ação sensível (cancelar reserva, alterar preço, mudar responsável) sem confirmação explícita do usuário.
- **Descrição:** distinguir tools de **consulta** (executam direto) de tools de **ação** (pausam o grafo em um nó de confirmação, retornando ao usuário uma proposta de ação para aprovar/recusar antes de prosseguir); usar o mecanismo de interrupt do LangGraph estudado em FASE9-EST-01.
- **Pré-requisitos:** FASE9-EST-01 (herdado).
- **Dependências:** FASE9-IMPL-02.
- **Resultado esperado:** qualquer pedido do tipo "cancele a reserva do lote X" resulta em uma pergunta de confirmação antes de executar, nunca execução direta.
- **Critérios de aceite:** teste garante que uma tool de ação nunca é executada sem uma etapa de confirmação explícita registrada; ação confirmada gera entrada de auditoria (reaproveitando o módulo `audit` da Fase 1) identificando que foi originada pelo agente.
- **Paralelizável:** Não pode ser finalizada sem FASE9-IMPL-02.
- **Conhecimentos novos introduzidos:** padrão human-in-the-loop com LangGraph, distinção tool de consulta vs. tool de ação.

## Épico E9.4 — Interface de conversa

### FASE9-IMPL-04 — Tela de chat com o agente (mobile)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** usuário conversa com o agente pelo app, incluindo o fluxo de confirmação.
- **Descrição:** reaproveitar a tela de pergunta da Fase 7 (FASE7-IMPL-05), evoluindo para formato de chat com histórico de mensagens e suporte a um card de confirmação (aceitar/recusar) quando o agente pausar aguardando aprovação.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE9-IMPL-03, FASE7-IMPL-05.
- **Resultado esperado:** conversa completa (pergunta → resposta, e pedido de ação → confirmação → execução) funcional no app.
- **Critérios de aceite:** as duas perguntas de exemplo do briefing funcionam ponta a ponta pelo app; um pedido de ação sensível exibe o card de confirmação corretamente.
- **Paralelizável:** Não pode ser finalizada sem FASE9-IMPL-03, mas o layout de chat pode ser adiantado com dado mockado.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE9-EST-01 → FASE9-IMPL-01 (tools) → FASE9-IMPL-03 (confirmação humana).
- **Dev 2:** FASE9-EST-01 → FASE9-IMPL-02 (grafo do agente) → FASE9-IMPL-04 (tela de chat).
- **Pontos de sincronização:**
  1. Schema de entrada/saída de cada tool (Pydantic) combinado antes de FASE9-IMPL-01 e FASE9-IMPL-02 avançarem em paralelo (Dev 2 pode mockar as tools com esse contrato).
  2. Formato do "card de confirmação" (o que o backend retorna quando o grafo pausa) combinado entre FASE9-IMPL-03 e FASE9-IMPL-04.
