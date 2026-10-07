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

#### Handoff (SCRUM-103)
- 10 tools implementadas em `app/ai_agents/application/tools.py` (schemas em `app/ai_agents/domain/schemas.py`): `consultar_lote`, `buscar_lotes`, `consultar_disponibilidade`, `lotes_de_esquina`, `lotes_proximos_de`, `lotes_dentro_de`, `distancia_entre_lotes`, `consultar_clientes`, `consultar_corretores`, `consultar_vendas`, `buscar_documentos`, `consultar_condicoes_comerciais`. Contrato fixado (não documentado antes): `async def tool(db, tenant_id, entrada: XInput) -> XOutput`, e toda exception de "não encontrado"/"inválido" vira `encontrado=False` + `mensagem` no output em vez de propagar — decisão necessária porque nada em `docs/` fixava isso antes desta task.
- `VendaService` citado na task não existe — é `ReservaService`; só `obter`/`obter_atual_por_lote` viraram tool de consulta (as demais mudam estado e ficam para FASE9-IMPL-03, human-in-the-loop).
- `LoteService.listar`/`GeoQueryService` não filtram por preço — `buscar_lotes` filtra em memória sobre o resultado.
- Testes em `backend/tests/test_ai_agents_tools.py` (12, um+ por tool) — padrão: `db_session` direto, sem HTTP, sem mock de DB (ver `docs/contexto-modulos/servicos-dominio.md`).
- Mapa completo dos serviços usados (`LoteService`, `GeoQueryService`, `ClienteService`, `CorretorService`, `ReservaService`, `BuscaService`) ficou registrado em `docs/contexto-modulos/servicos-dominio.md` — consultar antes de reexplorar esses módulos em FASE9-IMPL-02/03.

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

#### Handoff (SCRUM-104)
- `LLMProvider` (`app/ai_rag/infrastructure/llm_provider.py`) ganhou um terceiro método abstrato, `chat(mensagens, tools=None) -> ChatResposta`, via `POST /api/chat` do Ollama (tool calling nativo, não prompt-engineering) — decisão necessária porque a interface só tinha `embed`/`generate`. `ChatResposta`/`ToolCall` moram no mesmo arquivo. O agente reaproveita o singleton `ai_rag.llm_provider` (mesmo padrão de mock em teste: `monkeypatch.setattr(ai_rag, "llm_provider", mock)`).
- Grafo (`app/ai_agents/application/agente_service.py`, `AgenteService.perguntar`) é um laço `decidir -> executar_tool -> decidir` até o modelo responder sem propor tool (ou `MAX_CHAMADAS_TOOL=5`). Tools são resolvidas via `app/ai_agents/infrastructure/tool_registry.py` (novo arquivo) a partir dos schemas Pydantic de SCRUM-103 — `spec.input_model.model_json_schema()` vira o `parameters` do function-calling.
- Endpoint `POST /agente/perguntar`. Critério de aceite (as duas perguntas de exemplo) validado com o LLM mockado — o agente não gera SQL nem lida com "resolver nome para ID" (ex.: "área verde" → `feicao_id`) sozinho; isso pressupõe que a pergunta real (ou o histórico de conversa da Fase 9.4) já traga o identificador, já que nenhuma tool de SCRUM-103 faz esse lookup por nome.
- Dependência nova: `langgraph==0.2.60` (`requirements.txt`), que forçou bump de `httpx` de `0.25.1` para `0.28.1` (langgraph-sdk exige `httpx>=0.25.2`) — sem mudança de comportamento observada nos usos existentes de `httpx.AsyncClient`.
- **Gotcha de ambiente (não específica desta task, mas achada nela):** `backend/tests/test_rls.py` usa `TEST_APP_DATABASE_URL` (papel `lotiado_app`) com default `localhost:5432`; como o Postgres local costuma estar remapeado (ex.: `55499`, ver handoff SCRUM-71 nesse mesmo padrão), rodar a suíte sem exportar as duas envs corretas faz os testes de RLS/tenant-isolation falharem ou demorarem muito (connection refused). Rodar com:
  ```
  TEST_DATABASE_URL=postgresql+asyncpg://lotiado:lotiado@localhost:<porta>/lotiado_test
  TEST_APP_DATABASE_URL=postgresql+asyncpg://lotiado_app:lotiado_app@localhost:<porta>/lotiado_test
  ```
- Testes: `backend/tests/test_ai_agents_agente.py` (5 casos) — grafo com tool, "não encontrado" não vira invenção, resposta direta sem tool, resposta padrão quando modelo não gera texto, e o endpoint HTTP fim-a-fim.

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

#### Handoff (SCRUM-105)
- 3 tools de ação novas em `app/ai_agents/application/tools.py`: `cancelar_reserva` (`ReservaService.cancelar`), `alterar_preco_lote`/`alterar_responsavel_lote` (`LoteService.atualizar`) — mesmo contrato `async def tool(db, tenant_id, entrada) -> saida` das tools de consulta de SCRUM-103. `ToolSpec` (`tool_registry.py`) ganhou o campo `acao: bool = False`, marcado nessas três.
- Mecanismo de pausa: `langgraph.types.interrupt`/`Command(resume=...)`, com `MemorySaver` (checkpointer em memória, singleton do processo — decisão: suficiente para este demonstrador local de processo único; não sobrevive a restart nem escala para múltiplas réplicas). **Gotcha do LangGraph:** `Command(resume=False)` é tratado como "sem write" (`if cmd.resume:` internamente, e `False` é falsy) e faz o `ainvoke` explodir com `EmptyInputError` — resolvido embrulhando em `Command(resume={"aprovado": aprovado})`, que é truthy mesmo com `aprovado=False`.
- Grafo (`AgenteService`, `app/ai_agents/application/agente_service.py`) ganhou o nó `confirmar_acao`: quando `decidir` propõe uma tool com `spec.acao=True`, o roteamento (`_rotear_apos_decisao`) desvia para lá em vez de `executar_tool`. Só a primeira `tool_call` do turno é tratada como ação (mesma simplificação de "uma tool por turno" já assumida em SCRUM-104). `_chamar_tool` ganhou `permitir_acao: bool = False` como único ponto de execução real de qualquer tool — é essa flag (setada só depois da aprovação, dentro de `confirmar_acao`) que garante o critério de aceite "tool de ação nunca executa sem confirmação", não apenas o roteamento do grafo.
- `perguntar()`/novo `confirmar()` retornam `ResultadoAgente(resposta, confirmacao)` em vez de `str` — mudança de contrato de `AgenteService.perguntar()` (afeta quem chamava direto, ver testes atualizados de SCRUM-104). Endpoint `POST /agente/perguntar` ganhou `response_model_exclude_none=True` para manter `{"resposta": "..."}` quando não há confirmação pendente; novo endpoint `POST /agente/confirmar` (`confirmacao_id` + `aprovado`) resolve a pausa.
- Auditoria "originada pelo agente" (critério de aceite): **não** foi criada uma coluna nova em `audit_log` — `app/audit/domain/acoes.py` ganhou `OrigemAuditoria` (USUARIO/AGENTE) e `app/audit/infrastructure/context.py` um contextvar `_origem_atual` + `contexto_origem_auditoria(origem)`, lido em `tracking.py` e mesclado como chave `"origem"` dentro do `payload_depois` já existente (a "via de escape" que a própria docstring do módulo previa para payload que não vem de uma coluna). `AgenteService` só entra nesse contexto ao executar a tool de ação já aprovada; `usuario_id`/`tenant_id` continuam vindo do `AuditContextMiddleware` normal (quem confirmou é sempre o usuário autenticado da request).
- Segurança: `confirmar()` valida que `tenant_id` da request bate com o `tenant_id` persistido no estado pausado antes de retomar (`ConfirmacaoNaoEncontradaError` → 404 se não bater ou o `confirmacao_id` não existir/expirou) — sem isso, o `tenant_id` real usado na mutação viria do estado do grafo, não da request que está confirmando.
- Testes: `backend/tests/test_ai_agents_confirmacao.py` (5 casos: pausa sem executar, aprovação executa + audita com origem agente, recusa não executa, tenant errado falha, `confirmacao_id` inexistente falha) e novos casos em `test_ai_agents_tools.py` para as 3 tools de ação chamadas direto.

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

#### Handoff (SCRUM-106)

- `POST /agente/perguntar` inicia uma thread **nova a cada chamada** (`uuid4()` em `AgenteService.perguntar`) — o backend não mantém histórico de conversa entre perguntas distintas. O "histórico de mensagens" da tela de chat é puramente client-side (só exibição); cada envio de pergunta é independente do ponto de vista do grafo. Só a confirmação (`confirmacao_id` = `thread_id`) resume a mesma thread.
- `PerguntarAgenteResponse` usa `response_model_exclude_none=True` — `resposta`/`confirmacao` vêm **ausentes** (não `null`) quando `None`; o client (`mobile/src/api/agente.ts`) normaliza isso para `null` explícito antes de repassar ao componente.
- Tela evoluída em `mobile/app/assistente.tsx` (mesma rota que já existia da Fase 7): agora chama `/agente/*` em vez de `/rag/perguntar`, e ganhou um 4º tipo de mensagem (`confirmacao`) com card de aceitar/recusar; composer fica bloqueado enquanto há confirmação pendente. A resposta do agente é só texto (sem `fontes` — isso era específico do endpoint RAG antigo).
- Validado ponta a ponta (web, Playwright headless): pergunta simples e fluxo completo de ação sensível (pedido → card → recusar → resposta de acompanhamento). Ver nota de ambiente: nesta máquina o container `lotiado-postgres` estava com porta remapeada (55499→5432) divergindo do `backend/.env` versionado — não é algo desta task, mas quem for rodar o backend do zero aqui pode bater nisso.
- Arquivos-chave: `mobile/src/api/agente.ts` (novo), `mobile/app/assistente.tsx` (reescrito).

## Divisão de trabalho e sincronização

- **Dev 1:** FASE9-EST-01 → FASE9-IMPL-01 (tools) → FASE9-IMPL-03 (confirmação humana).
- **Dev 2:** FASE9-EST-01 → FASE9-IMPL-02 (grafo do agente) → FASE9-IMPL-04 (tela de chat).
- **Pontos de sincronização:**
  1. Schema de entrada/saída de cada tool (Pydantic) combinado antes de FASE9-IMPL-01 e FASE9-IMPL-02 avançarem em paralelo (Dev 2 pode mockar as tools com esse contrato).
  2. Formato do "card de confirmação" (o que o backend retorna quando o grafo pausa) combinado entre FASE9-IMPL-03 e FASE9-IMPL-04.
