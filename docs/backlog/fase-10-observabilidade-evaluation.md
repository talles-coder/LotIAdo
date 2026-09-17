# Fase 10 — Observabilidade & Evaluation de IA

Entrega desta fase: logging estruturado de todas as chamadas de IA (latência, tokens, modelo usado, contexto recuperado), e uma estratégia real de avaliação de qualidade para RAG e agentes — não apenas "parece funcionar" (risco registrado em [01-analise-requisitos.md](../01-analise-requisitos.md)).

## Épico E10.1 — Logging estruturado de IA

### FASE10-EST-01-D1 / FASE10-EST-01-D2 — Estudo: observabilidade de aplicações de IA (logging e tracing)
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender o que é relevante registrar em cada chamada de IA e como estruturar isso de forma consultável.
- **Conceitos a entender:** o que logar por chamada (prompt usado, modelo, tokens de entrada/saída, latência, contexto recuperado no RAG, erro se houver); logging estruturado (JSON) vs. texto livre, para permitir consulta depois; noção básica de tracing distribuído (OpenTelemetry) e por que é útil mesmo em um monólito (ver a cadeia completa de uma requisição: API → RAG → LLM).
- **Material recomendado:** documentação introdutória do OpenTelemetry para Python; documentação do `structlog` (ou `logging` padrão do Python configurado para saída JSON) para logging estruturado.
- **Exercício prático:** instrumentar uma função de exemplo que chama um LLM local, registrando prompt, tokens (se o modelo local expuser essa contagem) e latência em formato JSON estruturado.
- **Critério de conclusão:** exercício produz um log estruturado consultável (ex.: `jq` sobre o arquivo de log) com os campos relevantes.
- **Paralelizável:** Sim.

### FASE10-IMPL-01 — Logging estruturado em todas as chamadas de `LLMProvider`
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** toda chamada a `generate()`/`embed()` do `LLMProvider` (RAG da Fase 7, agente da Fase 9, importação da Fase 8) fica registrada de forma padronizada.
- **Descrição:** decorador ou wrapper na implementação de `LLMProvider` que registra, para cada chamada: timestamp, módulo de origem (rag/agente/importação), modelo usado, tokens de entrada/saída (quando disponível), latência, sucesso/erro; correlação com um `request_id` para reconstruir a cadeia completa de uma interação.
- **Pré-requisitos:** FASE10-EST-01-D1.
- **Dependências:** FASE7-IMPL-04, FASE9-IMPL-02, FASE8-IMPL-01 (já existem chamadas a instrumentar).
- **Resultado esperado:** log estruturado de todas as chamadas de IA, consultável.
- **Critérios de aceite:** uma pergunta ao RAG e uma pergunta ao agente geram logs completos e correlacionáveis pelo mesmo `request_id` entre os módulos envolvidos.
- **Paralelizável:** Sim, com FASE10-IMPL-02.
- **Conhecimentos novos introduzidos:** logging estruturado correlacionado, instrumentação transversal (wrapper/decorador).

### FASE10-IMPL-02 — Dashboard/consulta simples de métricas de IA
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** visualizar latência, volume de chamadas e taxa de erro de IA sem precisar ler logs brutos.
- **Descrição:** dado o volume pequeno esperado (projeto de portfólio, não produção real), uma tela simples no backoffice (Fase 5) que agrega os logs estruturados de FASE10-IMPL-01 (latência média, contagem por módulo, taxa de erro) é suficiente — **não introduzir Prometheus/Grafana** a menos que o volume real justifique (evitar complexidade desnecessária).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE10-IMPL-01, FASE5-IMPL-01.
- **Resultado esperado:** tela no backoffice com as métricas agregadas básicas.
- **Critérios de aceite:** tela reflete corretamente os logs gerados em um cenário de teste conhecido (N chamadas, M com erro).
- **Paralelizável:** Sim, com FASE10-IMPL-01 (pode ser desenvolvida contra logs de exemplo).
- **Conhecimentos novos introduzidos:** agregação simples de logs estruturados para exibição.

## Épico E10.2 — Avaliação de qualidade (RAG e agente)

### FASE10-EST-02-D1 / FASE10-EST-02-D2 — Estudo: avaliação de RAG e agentes (Ragas/promptfoo)
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender métricas de avaliação de RAG (faithfulness, relevância do contexto, relevância da resposta) e como comparar respostas de diferentes modelos/prompts de forma sistemática.
- **Conceitos a entender:** por que avaliação "no olho" não escala e some com a confiança na qualidade; métricas de faithfulness (a resposta é sustentada pelo contexto recuperado?) e relevância; conceito de "golden set" (perguntas com resposta/contexto esperado conhecido) para regressão; uso do Ragas para avaliar RAG e do promptfoo (ou equivalente open source) para comparar prompts/modelos lado a lado.
- **Material recomendado:** documentação oficial do Ragas; documentação oficial do promptfoo.
- **Exercício prático:** montar um golden-set de 5 perguntas/respostas esperadas sobre os documentos de teste já usados na Fase 7, e rodar Ragas sobre as respostas reais do sistema, registrando as métricas obtidas.
- **Critério de conclusão:** exercício produz um relatório (mesmo que simples) com métricas do Ragas para as 5 perguntas do golden-set.
- **Paralelizável:** Sim.

### FASE10-IMPL-03 — Golden-set de avaliação do RAG e do agente por tenant de teste
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** existir um conjunto de perguntas/respostas de referência, versionado no repositório, usado para detectar regressão de qualidade.
- **Descrição:** arquivo(s) de golden-set (ex.: YAML/JSON) com pergunta, resposta esperada (ou critério de aceitação), contexto esperado quando aplicável, cobrindo tanto perguntas de RAG (Fase 7) quanto de agente (Fase 9, incluindo as duas perguntas de exemplo do briefing).
- **Pré-requisitos:** FASE10-EST-02-D1.
- **Dependências:** FASE7-IMPL-04, FASE9-IMPL-02.
- **Resultado esperado:** golden-set versionado, pronto para ser executado por um script de avaliação.
- **Critérios de aceite:** golden-set cobre pelo menos 10 perguntas (RAG + agente combinados) com critério de aceitação claro para cada uma.
- **Paralelizável:** Sim, com FASE10-IMPL-04.
- **Conhecimentos novos introduzidos:** desenho de dataset de avaliação.

### FASE10-IMPL-04 — Script de avaliação automatizada (Ragas + promptfoo) rodável sob demanda
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** rodar a avaliação do golden-set com um comando único e obter um relatório de qualidade.
- **Descrição:** script que executa cada pergunta do golden-set contra o sistema real (RAG e agente), roda Ragas sobre os resultados de RAG, e permite comparação de prompts/modelos via promptfoo quando houver mais de uma configuração a comparar (ex.: dois modelos Ollama diferentes).
- **Pré-requisitos:** FASE10-EST-02-D2.
- **Dependências:** FASE10-IMPL-03.
- **Resultado esperado:** relatório de avaliação gerado a cada execução, comparável entre execuções ao longo do tempo.
- **Critérios de aceite:** rodar o script duas vezes com o mesmo golden-set produz métricas estáveis (não aleatórias além da variância esperada do LLM); uma regressão proposital (ex.: prompt pior) é detectada pela métrica de faithfulness caindo.
- **Paralelizável:** Não pode ser finalizada sem FASE10-IMPL-03, mas a estrutura do script pode ser adiantada.
- **Conhecimentos novos introduzidos:** execução automatizada de avaliação de IA, comparação de configurações (modelo/prompt).

## Divisão de trabalho e sincronização

- **Dev 1:** FASE10-EST-01/02 → FASE10-IMPL-01 (logging) → FASE10-IMPL-03 (golden-set).
- **Dev 2:** FASE10-EST-01/02 → FASE10-IMPL-02 (dashboard) → FASE10-IMPL-04 (script de avaliação).
- **Pontos de sincronização:** formato do log estruturado (FASE10-IMPL-01) combinado com Dev 2 antes de FASE10-IMPL-02 ser desenvolvida contra o formato real (pode usar exemplo mockado até lá).
