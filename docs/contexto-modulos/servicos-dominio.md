# Serviços de aplicação dos módulos de domínio (loteamentos_lotes, geo, clientes, corretores, vendas_reservas, ai_rag)

Levantado durante SCRUM-103 (FASE9-IMPL-01, tools de consulta do agente).
Todo serviço recebe `db: AsyncSession` no construtor e todo método recebe
`tenant_id: UUID` como primeiro parâmetro — RLS/escopo por tenant é reforçado
em cada query do repositório, não só no service.

## Serviços de aplicação

### LoteService — `backend/app/loteamentos_lotes/application/lote_service.py`
- `criar(tenant_id, loteamento_id, identificacao, quadra=None, area_m2=None, preco=None, caracteristicas=None) -> Lote`
- `listar(tenant_id, loteamento_id) -> list[Lote]` — todos os lotes ativos do loteamento, sem filtro extra
- `obter(tenant_id, lote_id) -> Lote` — levanta `LoteNaoEncontradoError`
- `atualizar(tenant_id, lote_id, quadra=None, area_m2=None, preco=None, caracteristicas=None, corretor_id=None, cliente_id=None) -> Lote`
- `transicionar_status(tenant_id, lote_id, novo_status: LoteStatus) -> Lote` — valida via `transicao_e_permitida()`
- `atualizar_geometria(tenant_id, lote_id, geometria: dict) -> Lote` — GeoJSON Polygon, SRID 4326
- `remover(tenant_id, lote_id) -> None` — soft delete

`Lote` (`domain/models.py`): `id, tenant_id, loteamento_id, identificacao, quadra, area_m2 (Decimal), preco (Decimal), status (LoteStatus), caracteristicas (dict), corretor_id, cliente_id, geometria (Polygon SRID 4326), deleted_at`.
`LoteStatus` (`domain/state_machine.py`): `DISPONIVEL, RESERVADO, VENDIDO, INDISPONIVEL`.
`listar()` não tem filtro por status/área/preço — quem precisa disso filtra em memória sobre o resultado (feito assim nas tools de FASE9-IMPL-01) ou usa `GeoQueryService` (que já combina status/área com filtro espacial).

### GeoQueryService — `backend/app/geo/application/geo_query_service.py` (Fase 4)
> Docstring do próprio módulo já avisa: "reutilizável — API REST hoje, agente de IA na Fase 9".
- `distancia_entre_lotes(tenant_id, lote_a_id, lote_b_id) -> float` (metros) — levanta `LoteNaoEncontradoError`/`LoteSemGeometriaError`
- `lotes_de_esquina(tenant_id, loteamento_id, status=None, area_m2_min=None) -> list[Lote]` — toca ≥2 ruas
- `lotes_proximos_de(tenant_id, feicao_id, raio_m, status=None, area_m2_min=None) -> list[Lote]` — levanta `FeicaoNaoEncontradaError`
- `lotes_dentro_de(tenant_id, area_geojson: dict, loteamento_id=None, status=None, area_m2_min=None) -> list[Lote]` — levanta `AreaInvalidaError`

Nenhum método filtra por **preço** — só `status`/`area_m2_min`. `FeicaoReferencia` (`app/geo/domain/models.py`): `tenant_id, loteamento_id, tipo (TipoFeicao: RUA/AREA_VERDE/OUTRO), nome, geometria (SRID 4326)`.

### ClienteService — `backend/app/clientes/application/cliente_service.py`
- `criar(tenant_id, nome, documento, contato) -> Cliente`
- `listar(tenant_id) -> list[Cliente]`
- `obter(tenant_id, cliente_id) -> Cliente` — levanta `ClienteNaoEncontradoError`
- `atualizar(...)`, `remover(...)` (soft delete)

### CorretorService — `backend/app/corretores/application/corretor_service.py`
- Mesmo shape do ClienteService: `criar`, `listar(tenant_id)`, `obter` (levanta `CorretorNaoEncontradoError`), `atualizar`, `remover`.

### ReservaService — `backend/app/vendas_reservas/application/reserva_service.py`
(não existe classe "VendaService" — reserva e venda são o mesmo registro `ReservaVenda`, `tipo`/`status` mudam in-place)
- `criar_reserva(tenant_id, lote_id, cliente_id, corretor_id=None) -> ReservaVenda` — **ação sensível**, muda status do lote, faz commit
- `obter(tenant_id, reserva_id) -> ReservaVenda` — consulta pura, levanta `ReservaNaoEncontradaError`
- `obter_atual_por_lote(tenant_id, lote_id) -> ReservaVenda` — consulta pura, levanta `ReservaNaoEncontradaError`
- `converter_para_venda(tenant_id, reserva_id) -> ReservaVenda` — **ação sensível**
- `cancelar(tenant_id, reserva_id) -> ReservaVenda` — **ação sensível**

Só `obter`/`obter_atual_por_lote` são consulta; as demais mudam estado e — por decisão de FASE9-IMPL-03 — devem passar por human-in-the-loop quando expostas ao agente, não virar tool de consulta direta.
`ReservaVenda`: `id, tenant_id, lote_id, cliente_id, corretor_id, tipo (RESERVA/VENDA), status (RESERVADO/VENDIDO/CANCELADA), created_at`.

**Gotcha:** sem `db.refresh()` depois do commit, de propósito — `expire_on_commit=False` e um `refresh()` abriria nova transação sem `app.tenant_id` setado, derrubando a query por RLS (ver comentário no topo do próprio arquivo e `app/tenancy/TENANT_CONVENTION.md`).

### BuscaService (RAG) — `backend/app/ai_rag/application/busca_service.py` (Fase 7)
- `buscar(tenant_id, pergunta, loteamento_id=None, lote_id=None, top_k=5) -> list[ResultadoBusca]` — gera embedding via `ai_rag.llm_provider.embed()`, busca chunks similares. Levanta `LoteamentoDaBuscaNaoEncontradoError`/`LoteDaBuscaNaoEncontradoError`.
- Endpoint `POST /rag/buscar` (`ai_rag/interface/routers.py`) só chama esse serviço — para reaproveitar em código (ex.: tool de agente), instancie `BuscaService(db)` direto, não vá por HTTP.
- `LLMProvider` (`ai_rag/infrastructure/llm_provider.py`) é abstrato (`embed`, `generate`, `chat`); instância singleton em `app/ai_rag/__init__.py` como `ai_rag.llm_provider` (hoje `OllamaLLMProvider`). Testes fazem `monkeypatch.setattr(ai_rag, "llm_provider", mock)`.
  - `chat(mensagens, tools=None) -> ChatResposta` (adicionado em FASE9-IMPL-02/SCRUM-104): tool calling via `POST /api/chat` do Ollama. `ChatResposta(conteudo, tool_calls: list[ToolCall])`, `ToolCall(id, nome, argumentos)`. Reaproveitado pelo agente (`app/ai_agents/`) — não é exclusivo do RAG, mora em `ai_rag` só porque é onde o singleton `llm_provider` já existia.

## Padrão de teste (services chamados direto, sem HTTP)

Fixtures em `backend/tests/conftest.py`: `db_session` (Postgres de teste real, sem mocks de DB) e `client` (AsyncClient com `app.dependency_overrides`). Para testar um service/tool diretamente:

```python
tenant = Tenant(name=slug, slug=slug)
db_session.add(tenant)
await db_session.commit()
# ... cria entidades de domínio direto via db_session.add(...) + commit ...
service = LoteService(db_session)
resultado = await service.obter(tenant.id, lote.id)
```

Não é preciso montar contexto de RLS manualmente (`SET LOCAL app.tenant_id`) nesses testes — o usuário de teste do Postgres bypassa RLS quando a sessão é usada direto (sem passar por `get_tenant_scoped_db`). Exemplos: `backend/tests/test_vendas_reservas.py` (linha ~375), `backend/tests/test_geo_queries.py`, `backend/tests/test_ai_agents_tools.py`.

Para tools que chamam RAG (`BuscaService`), mocke `ai_rag.llm_provider` com `AsyncMock()` para não depender do Ollama real — ver `backend/tests/test_ai_rag_busca.py` e `test_ai_agents_tools.py::test_buscar_documentos`.

## Tools de agente (FASE9-IMPL-01, `app/ai_agents/`)

Schemas de entrada/saída: `app/ai_agents/domain/schemas.py`. Funções: `app/ai_agents/application/tools.py`. Convenção fixada nessa task (não documentada em `docs/` antes disso): cada tool é `async def nome(db, tenant_id, entrada: XInput) -> XOutput`; exceptions de "não encontrado"/"inválido" são capturadas dentro da tool e viram `encontrado=False` + `mensagem` no output — nunca propagam para o chamador (o agente não deve receber um traceback, e sim uma resposta estruturada de "não achei").

## Grafo do agente (FASE9-IMPL-02/SCRUM-104, `app/ai_agents/`)

- `AgenteService` (`app/ai_agents/application/agente_service.py`) — `perguntar(tenant_id, pergunta) -> str`. `StateGraph` (LangGraph) com 3 nós: `decidir` (chama `ai_rag.llm_provider.chat` com as tools) → `executar_tool` (se o modelo pediu tool_calls) → volta a `decidir`; sem tool_calls, vai a `formatar_resposta` → `END`. Laço limitado por `MAX_CHAMADAS_TOOL` (5) para não travar se o modelo insistir em chamar tools.
- `app/ai_agents/infrastructure/tool_registry.py` — `TOOL_SPECS`/`TOOLS_POR_NOME` ligam o nome exposto ao LLM à função em `tools.py` e ao schema de entrada; `specs_para_llm()` gera o formato `{"type": "function", "function": {...}}` esperado por `LLMProvider.chat`.
- Endpoint `POST /agente/perguntar` (`app/ai_agents/interface/routers.py`) — só pergunta + resposta em texto; não expõe histórico de mensagens nem tool calls (isso é estado interno do grafo, recriado a cada chamada).
- Argumentos de tool propostos pelo modelo são validados via `spec.input_model.model_validate(argumentos)`; `ValidationError` vira mensagem de tool "parâmetros inválidos" (não propaga) — mas erro de negócio real dentro da tool (ex.: falha de infra) propaga normalmente, não é mascarado.
- Teste: `backend/tests/test_ai_agents_agente.py` — mocka só `ai_rag.llm_provider.chat` (via `AsyncMock().side_effect` com uma lista de `ChatResposta`, uma por "turno" do laço decidir→tool→decidir); tools e DB são reais, mesmo padrão de `db_session` direto do restante da suíte.
