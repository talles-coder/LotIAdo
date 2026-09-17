# Backlog — Como ler estes documentos

Um arquivo por fase (`fase-N-*.md`), cada um estruturado como **Épicos → Stories/Tasks → Subtasks**. Este README define o formato comum, para não repetir a explicação em cada arquivo.

## IDs

`FASEn-EST-xx` = task de estudo da Fase n. `FASEn-IMPL-xx` = task de implementação da Fase n. Quando uma task de estudo é duplicada para os dois devs, o ID leva um sufixo `-D1`/`-D2` (ex.: `FASE0-EST-01-D1`, `FASE0-EST-01-D2`) — mesmo conteúdo de estudo, exercício pode variar.

## Formato de task de estudo

- **Tipo:** Estudo
- **Dev:** Dev 1 / Dev 2 (sempre duplicada — ambos passam pelo mesmo conceito)
- **Objetivo:** o que o dev deve conseguir explicar/fazer ao final
- **Conceitos a entender:** lista curta e objetiva
- **Material recomendado:** documentação oficial / artigos — priorizando fontes gratuitas
- **Exercício prático:** pequeno, isolado do projeto principal quando possível (não bloqueia o repo)
- **Critério de conclusão:** objetivo e verificável (ex.: "consegue explicar X e Y", "exercício roda e produz Z")
- **Paralelizável:** Sim, sempre (as duas tasks de estudo, uma por dev, rodam ao mesmo tempo, sem depender uma da outra)

## Formato de task de implementação

- **Tipo:** Implementação
- **Dev responsável:** Dev 1 / Dev 2 / qualquer um
- **Objetivo**
- **Descrição**
- **Pré-requisitos:** inclui a(s) task(s) de estudo correspondente(s) — nenhuma task de implementação de um conceito novo começa sem o estudo antecedente ter sido concluído por quem for executá-la
- **Dependências:** outras tasks de implementação que precisam estar prontas antes (contratos, schemas, endpoints)
- **Resultado esperado**
- **Critérios de aceite:** verificáveis (testes passam, endpoint responde X, etc.)
- **Paralelizável:** Sim/Não — e com qual outra task, se sim
- **Conhecimentos novos introduzidos**

## Regra de estudo antes de implementação

Sempre que uma story de implementação introduz uma tecnologia/conceito novo para o projeto (ex.: RLS, PostGIS, LangGraph, pgvector/embeddings, RBAC, Redis/RQ, Expo for Web, MinIO, OpenTelemetry, IaC), ela é precedida por duas tasks de estudo equivalentes (`-D1`/`-D2`) e as declara como pré-requisito. O objetivo é *just-in-time*: a task de estudo só é **executada** perto do momento em que a implementação vai começar de fato — mas o planejamento (o quê estudar, com quê, e o exercício) já está pronto agora, para os dois devs poderem se organizar sem esperar planejamento adicional.

## Paralelização entre Dev 1 e Dev 2

Cada arquivo de fase tem uma seção "Divisão de trabalho e sincronização" ao final, explicitando: o que cada dev pode fazer sem esperar o outro, e os pontos exatos em que os dois precisam alinhar um contrato (schema de API, formato de evento, nome de tabela) antes de seguir. Interfaces/contratos que evitam bloqueio mútuo são declarados explicitamente nas tasks (ex.: "contrato de resposta do endpoint X definido em OpenAPI antes de o mobile consumir").
