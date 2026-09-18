# Fase 7 — Documentos + RAG

Entrega desta fase: usuários fazem perguntas em linguagem natural sobre os documentos de um tenant (memorial, contratos, tabelas de preço, etc.) e recebem respostas com citação da fonte. RAG construído "na mão" contra pgvector primeiro (decisão D5 em [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md)); LlamaIndex entra só depois, como comparação.

## Épico E7.1 — Fundamentos de embeddings e busca vetorial

### FASE7-EST-01-D1 / FASE7-EST-01-D2 — Estudo: embeddings e busca por similaridade vetorial
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender o que é um embedding, como medir similaridade, e como o pgvector armazena/indexa isso.
- **Conceitos a entender:** embedding como vetor de números representando significado semântico; similaridade de cosseno vs. distância euclidiana; dimensionalidade do vetor (depende do modelo escolhido); índice `IVFFlat`/`HNSW` no pgvector e o trade-off velocidade/precisão; por que buscar "os k mais próximos" não garante que sejam de fato relevantes (a busca vetorial é um filtro, não a resposta final).
- **Material recomendado:** documentação oficial do `pgvector` (tipos de índice, operadores de distância `<->`/`<=>`); artigo introdutório sobre embeddings (ex.: documentação da OpenAI ou Sentence-Transformers sobre "what are embeddings", usado apenas como material conceitual gratuito, não implica usar a API paga).
- **Exercício prático:** em um banco de teste com pgvector, gerar embeddings de 5-10 frases curtas (usando qualquer modelo local disponível), inserir e rodar uma busca por similaridade, conferindo manualmente se os resultados fazem sentido semântico.
- **Critério de conclusão:** consegue explicar a diferença entre os operadores de distância do pgvector e mostrar a busca funcionando no exercício.
- **Paralelizável:** Sim.

### FASE7-EST-02-D1 / FASE7-EST-02-D2 — Estudo: RAG (Retrieval-Augmented Generation) e chunking
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender o pipeline completo de RAG e as estratégias de chunking de documentos.
- **Conceitos a entender:** pipeline geral (ingestão → chunking → embedding → indexação → retrieval → geração aumentada por contexto); estratégias de chunking (por tamanho fixo com overlap, por estrutura do documento — parágrafos/seções); trade-off entre chunk muito pequeno (perde contexto) e muito grande (dilui relevância); necessidade de manter a referência à fonte (documento/página) em cada chunk para poder citar depois.
- **Material recomendado:** documentação do LangChain sobre `text splitters` (usada aqui apenas como referência conceitual, mesmo implementando manualmente na FASE7-IMPL-02); artigos introdutórios sobre RAG (ex. documentação da Anthropic ou Pinecone sobre RAG, como material conceitual gratuito).
- **Exercício prático:** pegar um documento de texto de exemplo (2-3 páginas), aplicar duas estratégias de chunking diferentes manualmente/com script, e comparar o resultado da recuperação para a mesma pergunta em cada uma.
- **Critério de conclusão:** consegue explicar por que uma estratégia de chunking recuperou um contexto melhor que a outra no exercício.
- **Paralelizável:** Sim.

## Épico E7.2 — Pipeline de ingestão de documentos

### FASE7-EST-03-D1 / FASE7-EST-03-D2 — Estudo: filas de job com Redis + RQ
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender Redis como broker de fila na prática (decisão D3 em [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md)) e como estruturar um worker RQ para processar jobs de ingestão sem bloquear a requisição HTTP.
- **Conceitos a entender:** Redis como estrutura de dados usada como fila (lista/stream por trás do RQ); processo `worker` separado do processo da API, consumindo jobs da fila; enfileirar um job (`queue.enqueue(...)`) a partir de uma rota FastAPI; retry e status de job (`queued`/`started`/`finished`/`failed`); idempotência (reindexar o mesmo documento duas vezes não deve duplicar chunks — reaproveita a lógica de FASE7-IMPL-02).
- **Material recomendado:** documentação oficial do RQ (rq.readthedocs.io); documentação do Redis sobre listas/streams como estrutura de fila (nível conceitual, não é necessário se aprofundar em Redis além do que RQ usa).
- **Exercício prático:** função de exemplo (ex.: "processar" uma string com um `time.sleep` simulando trabalho pesado) enfileirada via RQ a partir de um script, executada por um worker rodando em outro terminal/processo, com o status do job consultado via API do RQ.
- **Critério de conclusão:** exercício enfileira, processa e consulta o status de um job de ponta a ponta, com o worker rodando como processo separado.
- **Paralelizável:** Sim.

### FASE7-IMPL-01 — Chunking e geração de embeddings na ingestão de documentos (via fila RQ)
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** todo documento enviado (Fase 5) é automaticamente dividido em chunks e indexado como embeddings, processado de forma assíncrona por um worker RQ — não bloqueando a requisição de upload.
- **Descrição:** usar `LangChain` apenas para os `text splitters` (ex.: `RecursiveCharacterTextSplitter`), conforme decisão D5; ao final do upload (Fase 5), a rota enfileira um job RQ (`processar_documento(documento_id)`) em vez de processar inline; o worker, rodando como serviço próprio no docker-compose, consome o job, gera embedding de cada chunk via `LLMProvider.embed()` (Ollama), e persiste em uma tabela `document_chunks` com coluna `vector` (pgvector), texto do chunk, `documento_id`, `tenant_id`, `loteamento_id`/`lote_id` herdados do documento; status de indexação do documento (`pendente`/`processando`/`concluído`/`falhou`) consultável pela tela de documentos.
- **Pré-requisitos:** FASE7-EST-01-D1, FASE7-EST-02-D1, FASE7-EST-03-D1.
- **Dependências:** FASE5-IMPL-04 (documentos existem), FASE0 (LLMProvider/Ollama, Redis já disponível desde o docker-compose).
- **Resultado esperado:** upload de um documento enfileira o processamento; um serviço `worker` separado do backend processa e atualiza o status.
- **Critérios de aceite:** após upload de um documento de teste, o job aparece na fila, é processado pelo worker, e `document_chunks` contém entradas com embeddings não-nulos e metadados de escopo corretos; a rota de upload responde imediatamente (não espera o processamento terminar).
- **Paralelizável:** Sim, com FASE7-IMPL-02 (que pode ser desenvolvida contra chunks inseridos manualmente até esta task terminar).
- **Conhecimentos novos introduzidos:** `LangChain text splitters`, geração de embeddings em lote, fila RQ/Redis com worker separado (primeira aplicação prática de D3).

### FASE7-IMPL-02 — Reindexação ao atualizar/substituir documento
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** ao substituir um documento, os chunks antigos são removidos e os novos gerados — sem duplicar nem deixar lixo indexado.
- **Descrição:** endpoint de substituição de documento que remove `document_chunks` antigos do `documento_id` e dispara o pipeline de FASE7-IMPL-01 novamente.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE7-IMPL-01.
- **Resultado esperado:** reindexação idempotente e sem duplicação.
- **Critérios de aceite:** substituir um documento de teste duas vezes seguidas resulta sempre no número correto de chunks (sem acúmulo).
- **Paralelizável:** Não pode ser finalizada sem FASE7-IMPL-01, mas o endpoint de substituição em si pode ser esboçado em paralelo.
- **Conhecimentos novos introduzidos:** nenhum além de FASE7-IMPL-01.

## Épico E7.3 — Busca semântica e geração de resposta

### FASE7-IMPL-03 — Endpoint de busca semântica com filtro de escopo
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** dado uma pergunta, retornar os chunks mais relevantes, respeitando tenant e, opcionalmente, loteamento/lote.
- **Descrição:** `POST /rag/buscar` recebe pergunta + escopo opcional; gera embedding da pergunta; consulta pgvector com filtro de `tenant_id` **explícito na query** (defesa em profundidade além da RLS, conforme [01-analise-requisitos.md](../01-analise-requisitos.md)) e, se informado, `loteamento_id`/`lote_id`.
- **Pré-requisitos:** FASE7-EST-01-D2.
- **Dependências:** FASE7-IMPL-01.
- **Resultado esperado:** endpoint retorna os top-k chunks com score de similaridade e metadados de origem (documento, página se disponível).
- **Critérios de aceite:** teste com dois tenants de teste confirma que a busca de um nunca retorna chunk do outro, mesmo com a mesma pergunta.
- **Paralelizável:** Sim, com FASE7-IMPL-04 (que consome esta busca, mas pode ser desenhada em paralelo com um contrato combinado).
- **Conhecimentos novos introduzidos:** filtro de metadados combinado com busca vetorial.

### FASE7-IMPL-04 — Geração de resposta com citação de fonte
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** resposta final em linguagem natural, citando os documentos usados.
- **Descrição:** `POST /rag/perguntar` chama FASE7-IMPL-03, monta um prompt com a pergunta + os chunks recuperados, chama `LLMProvider.generate()`, e retorna a resposta junto com a lista de documentos/trechos usados como fonte.
- **Pré-requisitos:** nenhum estudo novo além de FASE7-EST-02.
- **Dependências:** FASE7-IMPL-03.
- **Resultado esperado:** endpoint de pergunta-resposta funcional, citando fontes.
- **Critérios de aceite:** para uma pergunta sobre um documento de teste conhecido, a resposta cita corretamente o documento de origem; para uma pergunta sem contexto relevante disponível, o sistema responde que não encontrou informação em vez de inventar (checado manualmente/no golden-set da Fase 10).
- **Paralelizável:** Não pode ser finalizada sem FASE7-IMPL-03.
- **Conhecimentos novos introduzidos:** prompt com contexto recuperado (grounding), formatação de resposta com citação.

## Épico E7.4 — Interface de consulta

### FASE7-IMPL-05 — Tela de perguntas sobre documentos (mobile e/ou backoffice)
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** usuário final consegue fazer a pergunta e ver a resposta com as fontes.
- **Descrição:** tela simples de chat/pergunta única no mobile (reaproveitável depois pela Fase 9 de agentes) que chama `POST /rag/perguntar` e exibe resposta + fontes como links/referências.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE7-IMPL-04.
- **Resultado esperado:** tela funcional consumindo o endpoint de RAG.
- **Critérios de aceite:** pergunta de teste retorna resposta visível com pelo menos uma fonte listada quando aplicável.
- **Paralelizável:** Não pode ser finalizada sem FASE7-IMPL-04, mas o layout da tela pode ser feito em paralelo com dado mockado.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto na Fase 3.

## Épico E7.5 — Comparação com LlamaIndex (estudo aplicado)

### FASE7-EST-04-D1 / FASE7-EST-04-D2 — Estudo: LlamaIndex como alternativa ao RAG manual
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** depois de já ter construído o RAG manualmente (FASE7-IMPL-01 a 04), entender o que o LlamaIndex resolveria/simplificaria.
- **Conceitos a entender:** abstrações do LlamaIndex (`Document`, `Index`, `QueryEngine`); como ele lida com chunking, embeddings e retrieval "prontos"; onde ele se encaixaria no pipeline já construído (substituindo ou complementando partes específicas).
- **Material recomendado:** documentação oficial do LlamaIndex (quickstart).
- **Exercício prático:** reimplementar, em um script isolado (não substituindo o pipeline do produto), a mesma busca da FASE7-IMPL-03 usando LlamaIndex sobre os mesmos documentos de teste, e comparar linhas de código e resultado.
- **Critério de conclusão:** documento curto (pode ser um comentário no PR ou uma nota em `docs/03-decisoes-tecnicas.md`) registrando o que o LlamaIndex economizaria e se valeria a pena migrar.
- **Paralelizável:** Sim. Esta task não bloqueia nenhuma implementação — é aprendizado aplicado, não entra no roadmap crítico.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE7-EST-01/02/03 → FASE7-IMPL-01 (chunking/embeddings + fila RQ) → FASE7-IMPL-03 (busca) → FASE7-IMPL-05 (tela).
- **Dev 2:** FASE7-EST-01/02/03 → FASE7-IMPL-02 (reindexação) → FASE7-IMPL-04 (geração de resposta).
- **Pontos de sincronização:**
  1. Schema de `document_chunks` (colunas, tipo do vetor, dimensão do embedding — depende do modelo escolhido em D6) combinado antes de FASE7-IMPL-01/02 avançarem.
  2. Serviço `worker` (RQ) adicionado ao docker-compose e nome/formato do job (`processar_documento(documento_id)`) combinados antes de FASE7-IMPL-01/02 avançarem em paralelo.
  3. Contrato de resposta de `POST /rag/buscar` (FASE7-IMPL-03) combinado com Dev 2 antes de FASE7-IMPL-04 ser implementada, para poderem correr em paralelo com stub.
  4. FASE7-EST-04 (LlamaIndex) só faz sentido depois que FASE7-IMPL-01 a 04 estiverem prontas — não é bloqueante, mas é logicamente posterior.
