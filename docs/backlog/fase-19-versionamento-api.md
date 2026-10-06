# Fase 19 — Versionamento de API

Entrega desta fase: convenção de versionamento aplicada de fato, com um exercício real de mudança incompatível, para que um app de campo desatualizado não quebre sem aviso quando o backend evoluir. Fecha a decisão D14 (estratégia de versionamento) de `03-decisoes-tecnicas.md`: **versionamento por header** (`Accept: application/vnd.lotiado.v2+json`), decidido em 2026-09-27 — não por path. Entra depois de todo o domínio+comercial estar pronto (Fases 0–18) — só faz sentido versionar uma API já estável.

## Épico E19.1 — Fundamentos

### FASE19-EST-01-D1 / FASE19-EST-01-D2 — Estudo: versionamento de API REST por header (content negotiation)
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como aplicar versionamento por header (D14) no FastAPI sem duplicar lógica de negócio.
- **Conceitos a entender:** content negotiation via header `Accept` (o mesmo path responde formatos diferentes conforme o header enviado, em vez de rotas `/v1/`, `/v2/` separadas); `Depends` do FastAPI para extrair a versão solicitada do header e escolher o serializador/schema de resposta correto; versão padrão quando o client não envia o header (deve ser a mais antiga suportada, nunca a mais nova — client desatualizado não pode "ganhar" um formato que não entende); estratégia de depreciação (por quanto tempo a v1 continua sendo aceita depois da v2 existir).
- **Material recomendado:** documentação oficial do FastAPI sobre `Depends`/dependências de rota; artigos conceituais sobre "API versioning via Accept header"/content negotiation (nível conceitual, não é uma feature nativa do FastAPI, é um padrão a implementar por cima).
- **Exercício prático:** num projeto de exemplo isolado, um único endpoint (`GET /item`) que retorna formato de resposta diferente conforme o header `Accept` enviado (`vnd.exemplo.v1+json` vs. `vnd.exemplo.v2+json`), reaproveitando o mesmo service por baixo dos dois.
- **Critério de conclusão:** o mesmo endpoint responde nos dois formatos conforme o header, sem duplicar a lógica de negócio; D14 já estava decidida (header) antes desta task — o estudo é sobre a técnica de implementação, não sobre escolher a estratégia.
- **Paralelizável:** Sim.

## Épico E19.2 — Aplicação

### FASE19-IMPL-01 — Negociação de versão por header + versão v1 explícita
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** toda rota existente passa a responder explicitamente como "v1" via negociação de header, sem quebrar nenhum client atual (app mobile já em uso, que hoje não envia o header).
- **Descrição:** dependência comum (`resolver_versao_api`) que lê o header `Accept`, extrai a versão solicitada (`application/vnd.lotiado.vN+json`) e, se ausente ou não reconhecida, assume v1 (o formato já em uso hoje — client antigo continua funcionando sem precisar saber que versionamento existe); cada rota passa a ter um schema de resposta "v1" nomeado explicitamente, mesmo que hoje só exista essa versão.
- **Pré-requisitos:** FASE19-EST-01-D1.
- **Dependências:** toda a API já existente das fases anteriores.
- **Resultado esperado:** toda rota responde no formato v1 por padrão (app mobile atual não muda nada); enviar o header com uma versão desconhecida não quebra a chamada (cai no fallback v1).
- **Critérios de aceite:** suíte de testes existente passa sem alteração de asserção, só passando a validar que o formato retornado é o "v1" nomeado.
- **Paralelizável:** Sim, com FASE19-IMPL-02 (que já pode ser desenhada em paralelo, mas só roda de fato depois desta).
- **Conhecimentos novos introduzidos:** nenhum além de FASE19-EST-01.

### FASE19-IMPL-02 — Exercício de mudança incompatível: v2 convivendo com v1 no mesmo endpoint
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** provar na prática que um app antigo (que não envia o header de versão, ou envia v1) continua funcionando quando uma mudança incompatível é introduzida na v2.
- **Descrição:** escolher um endpoint existente e mudar deliberadamente o formato de resposta de forma incompatível (ex.: renomear ou reestruturar um campo) só quando o header pedir v2, mantendo o mesmo path respondendo no formato antigo para quem não pede v2 explicitamente; os dois formatos reaproveitam o mesmo serviço de aplicação por baixo (adaptação de formato na camada de interface/serializador, não duplicação de regra de negócio).
- **Pré-requisitos:** nenhum estudo novo além de FASE19-EST-01.
- **Dependências:** FASE19-IMPL-01.
- **Resultado esperado:** um cliente de teste simulando o app "antigo" (sem header, ou `Accept: .../vnd.lotiado.v1+json`) continua funcionando sem nenhuma mudança, enquanto um cliente novo (`Accept: .../vnd.lotiado.v2+json`) já recebe o formato novo — no mesmo path, mesma URL.
- **Critérios de aceite:** teste automatizado chama o mesmo endpoint com os dois headers e valida que cada um retorna o formato esperado da sua versão; chamada sem header nenhum se comporta como v1 (não erro, não v2 por padrão).
- **Paralelizável:** Não pode ser finalizada sem FASE19-IMPL-01.
- **Conhecimentos novos introduzidos:** convivência real de duas versões de contrato sobre o mesmo path via negociação de header.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE19-EST-01 → FASE19-IMPL-01 (negociação de versão + v1 explícita).
- **Dev 2:** FASE19-EST-01 → FASE19-IMPL-02 (exercício v2, depende de IMPL-01 estar pronta).
- **Pontos de sincronização:** FASE19-IMPL-02 só começa depois que a dependência `resolver_versao_api` de FASE19-IMPL-01 estiver mesclada, para não haver conflito de implementação da mesma peça central.
