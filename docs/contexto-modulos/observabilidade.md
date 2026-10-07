# observabilidade

Criado em SCRUM-109 (FASE10-IMPL-01): logging estruturado das chamadas ao
`LLMProvider` (`app/ai_rag/infrastructure/llm_provider.py`), correlacionadas
por `request_id`. Só isso por enquanto — nenhuma outra métrica/tracing do app
passa por aqui ainda.

## Infraestrutura

### `OrigemChamadaIA` — `domain/chamada_ia.py`
`StrEnum`: `RAG`, `AGENTE`, `IMPORTACAO`, `DESCONHECIDA` (fallback quando nenhum
`contexto_origem_ia` está ativo — não deveria acontecer nos 5 call sites já
instrumentados, mas evita logar uma origem errada por omissão).

### `context.py` — contextvars, mesmo padrão de `app.audit.infrastructure.context`
- `request_id_atual() -> str | None` / `origem_ia_atual() -> OrigemChamadaIA | None`
- `contexto_request_id(request_id: str)` — usado só pelo `RequestIdMiddleware`
- `contexto_origem_ia(origem: OrigemChamadaIA)` — cada application service que
  chama `ai_rag.llm_provider.<embed|generate|chat>` envolve a chamada nisso.
  Call sites atuais: `busca_service.py`/`pergunta_service.py` (RAG),
  `agente_service.py._decidir` (AGENTE), `ingestao_service.py` (loop de chunks)
  e `mapeamento_sugestao_service.py` (IMPORTACAO).

### `llm_logging.py` — `medir_chamada_llm(*, metodo, modelo)` (context manager)
Cronometra a chamada, devolve um `dict` mutável (`tokens_entrada`/`tokens_saida`,
`None` por padrão — só `/api/generate` e `/api/chat` do Ollama devolvem
contagem, `/api/embeddings` não) pro chamador preencher, e loga um evento no
logger `app.ia` no `finally` (roda em sucesso e em erro; relança a exceção).
Usado dentro de `OllamaLLMProvider.embed/generate/chat` — não em cada call
site, que só precisa do `contexto_origem_ia`.

### `logging_config.py` — `configurar_logging_estruturado()`
Liga um `JsonFormatter` (uma linha JSON por `LogRecord`) no logger `app.ia`.
Chamado uma vez em `app.main` na subida da app. Idempotente (`if logger.handlers: return`).
**Não seta `propagate = False`** — deliberado, para que `caplog` (pytest) capture
os registros no teste sem precisar anexar handler próprio nesse logger.

### `RequestIdMiddleware` — `interface/middleware.py`
Gera (ou propaga `X-Request-Id` recebido) um id por request HTTP, via
`contexto_request_id`. Registrado em `app.main` junto com `AuditContextMiddleware`.
Correlaciona várias chamadas de LLM de uma mesma request (ex.: RAG faz
embed+generate; o agente decide em loop, várias `chat()`) — **não** correlaciona
`/agente/perguntar` com o `/agente/confirmar` que resume a mesma conversa depois
(são requests HTTP diferentes, cada uma ganha seu próprio `request_id`).

## Pegadinhas / não-óbvio

- `ingestao_service.py` roda no worker RQ (processo separado, `asyncio.run()`
  próprio) — nunca há `RequestIdMiddleware` ativo lá, então cada chunk embedado
  cai no fallback (`request_id` gerado ali mesmo em `medir_chamada_llm`), um
  por chamada. Não é bug: não há uma "request" pra correlacionar nesse caso.
- LangGraph (`agente_service.py`) roda os nós do grafo na mesma task asyncio da
  request original — os contextvars de `request_id`/`origem` propagam
  normalmente através de `_decidir` sem precisar de nada especial.

## Padrão de teste

`backend/tests/test_observabilidade_llm_logging.py` — só testes unitários
(sem BD): `caplog.set_level(logging.INFO, logger="app.ia")` + `caplog.records`
pra inspecionar o dict logado. Não testa `OllamaLLMProvider` em si (nenhum
outro teste do projeto mocka a chamada HTTP ao Ollama — sempre trocam
`app.ai_rag.llm_provider` inteiro via `monkeypatch`, ver skill `testing`).
