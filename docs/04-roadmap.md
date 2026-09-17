# 04 — Roadmap (Etapa 4)

Ordem incremental, cada fase entrega uma versão funcional demonstrável. Backlog detalhado de cada fase em `docs/backlog/fase-N-*.md`.

| Fase | Nome | Entrega funcional | Depende de |
|---|---|---|---|
| 0 | Fundamentos & scaffolding | Repo, docker-compose com todos os serviços de base, skeleton FastAPI, módulos `tenancy`+`identity` mínimos, testes de setup | — |
| 1 | MVP núcleo de domínio (single tenant) | CRUD completo de loteamentos/lotes/clientes/corretores/reservas/vendas com máquina de estados e auditoria básica, via API (sem GIS, sem mobile) | Fase 0 |
| 2 | Multi-tenancy real | RLS aplicado de fato, múltiplos tenants de teste isolados, convite/ativação de usuários, RBAC evoluído | Fase 1 |
| 3 | Mobile MVP | App React Native consumindo a API (auth, listas, detalhes, criar reserva/venda) — valida a pilha mobile isoladamente, sem mapa/offline ainda | Fase 2 |
| 4 | GIS | PostGIS, polígonos, mapa no mobile e no backoffice, importação de CSV manual (sem IA) | Fase 2 (pode rodar em paralelo com Fase 3) |
| 5 | Backoffice web mínimo (Expo for Web) | Import CSV, editor/revisão de polígono, gestão de documentos — rotas web do mesmo app Expo | Fase 4 (parcialmente paralelizável com Fase 3/4 — ver Etapa 7 de cada backlog) |
| 6 | Offline read-cache no mobile | Cache local + detecção de conectividade + bloqueio de escrita offline | Fase 3 |
| 7 | Documentos + RAG | Upload, chunking, embeddings, pgvector, busca semântica com citação de fonte. Primeira introdução real de Redis/RQ como fila de processamento assíncrono (decisão D3) | Fase 5 (documentos já geridos no backoffice) |
| 8 | IA para importação flexível | CSV sem padrão fixo via LLM, extração assistida de planta/imagem, sempre com revisão humana | Fase 4 e Fase 5; a extração de imagem reaproveita a fila RQ/worker introduzida na Fase 7 |
| 9 | Agentes com LangGraph | Tools sobre os serviços existentes, chat no mobile/web | Fase 7 (RAG como uma das tools) |
| 10 | Observabilidade & Evaluation de IA | Logging estruturado, métricas, golden-set de avaliação para RAG/agentes | Fase 7 e Fase 9 |
| 11 | Cloud/produção (AWS) | Deploy, CI/CD, IaC básico | Todas as anteriores funcionando localmente |

## Por que essa ordem

- **Domínio antes de GIS/mobile**: valida regras de negócio (estados, permissões, auditoria) antes de adicionar a complexidade de mapa e app mobile por cima.
- **Multi-tenancy antes de mobile/GIS**: isolamento de tenant é transversal — melhor testado cedo, antes de crescer a superfície de código que depende dele.
- **Mobile MVP sem mapa antes de GIS**: separa a validação da pilha mobile (auth, navegação, chamadas de API) da complexidade de mapa, permitindo os dois devs trabalharem em paralelo (um em GIS/backend, outro consolidando mobile) sem bloqueio mútuo.
- **RAG antes de Agentes**: o agente usa busca em documentos como uma de suas tools; construir RAG primeiro dá uma tool madura para o agente consumir.
- **Observabilidade por último entre os módulos de IA, não no fim do projeto**: entra logo depois de RAG e Agentes existirem (Fase 10), não é adiada até o final do roadmap inteiro — só a fase de Cloud/Produção fica de fato por último.
- **Cloud por último**: princípio geral do projeto é rodar tudo localmente/gratuito primeiro; migrar para AWS só depois de tudo validado localmente evita gastar créditos/tempo de cloud iterando sobre algo que ainda pode mudar.
