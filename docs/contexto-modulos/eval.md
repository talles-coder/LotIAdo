# eval (golden-set de avaliação de IA)

Criado em SCRUM-113 (FASE10-IMPL-03). Vive em `backend/eval/` +
`backend/scripts/seed_golden_set.py` — não é um módulo de `app/` (não sobe
com a API), é dado/ferramenta de desenvolvimento rodado sob demanda.

## Conteúdo

- `eval/ids.py` — IDs determinísticos (`uuid5` a partir de um nome fixo) do
  tenant/loteamento/lotes/feições/documento de teste. Nenhum UUID é gravado em
  disco/YAML — qualquer código que precise referenciar essas entidades importa
  as constantes daqui.
- `eval/config.py` — caminhos compartilhados (`GOLDEN_SET_PATH`, `REPORTS_DIR`).
- `eval/golden_set.yaml` — os casos de avaliação (pergunta, critério de
  aceitação, substrings esperadas). Formato documentado no cabeçalho do
  próprio arquivo.
- `scripts/seed_golden_set.py` (`python -m scripts.seed_golden_set`,
  idempotente) — cria o tenant `golden-set` com os dados que o golden-set
  espera: 1 loteamento, 2 ruas + 1 área verde (geometrias reais, mesmo padrão
  de `tests/test_ai_agents_tools.py`), 4 lotes (GE-01..GE-04, cobrindo
  esquina/não-esquina/perto-de-área-verde/vendido), 1 documento indexado com
  embeddings reais (requer Ollama local rodando).

## Por que "tenant de teste" é criado do zero, não reaproveita `demo`

`demo` (`docs/guia-rodar-android-nativo.md`) é construído manualmente pela app
ao longo do tempo — não é determinístico nem versionado, não dá pra saber sem
consultar o banco quais lotes/documentos existem lá agora. O golden-set precisa
de dados estáveis entre corridas (mesmo id sempre aponta pro mesmo dado), daí
o seed próprio.

## Por que perguntas de agente citam um ID, não só um nome

Nenhuma tool do agente resolve nome→id (já valia desde SCRUM-103/FASE9-IMPL-01,
mas só ficou óbvio rodando perguntas reais contra este golden-set —
`buscar_lotes`/`lotes_de_esquina` precisam de `loteamento_id: UUID`,
`consultar_lote`/`distancia_entre_lotes`/etc. precisam de `lote_id: UUID`,
nenhuma tool aceita a `identificacao` humana ("GE-01") nem o nome do
loteamento). Um golden-set que só citasse nomes começaria falhando sempre,
sem sinalizar nada útil. A maioria dos casos de agente usa placeholders
(`{loteamento_id}`, `{lote_ge_01}`, `{lote_ge_04}`, `{lote_inexistente}`)
resolvidos pelo script que roda a avaliação — testam a capacidade real (tool
call a partir de um id já conhecido), não uma resolução por nome que não
existe. Um caso (`agente-area-verde-limitacao-conhecida`) documenta esse gap
deliberadamente em vez de escondê-lo.

## `contem_todos` — como a checagem automática funciona

Lista de substrings (case-insensitive, todas precisam aparecer na resposta).
Lista vazia = caso sem checagem automática (revisão manual do
`criterio_aceitacao`) — 3 IDs simultâneos numa resposta de LLM é frágil
contra fraseado, então casos com múltiplos resultados esperados checam só o
primeiro item.

**Pegadinha:** frases como "não encontrei" vs. "não consegui encontrar" vs.
"não encontrou" não batem com uma substring contígua — os casos de "não
inventa" usam duas entradas separadas (`["não", "encontr"]`), não uma frase
única.

## Padrão de teste

`backend/tests/test_eval_golden_set.py` — estrutura do YAML (≥10 casos, campos
obrigatórios) e determinismo dos IDs. Não roda `seed_golden_set` de verdade
(precisa de Ollama + Postgres reais); validado manualmente (ver handoff de
SCRUM-113 no backlog).
