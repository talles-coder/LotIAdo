# 01 — Análise de Requisitos (Etapa 1)

> Este documento é a análise crítica do briefing original do projeto: lacunas, ambiguidades, riscos e decisões que precisavam ser tomadas antes de detalhar arquitetura e backlog. As decisões marcadas como **[RESOLVIDO]** foram discutidas e fechadas com o time; o restante são observações e recomendações — nada foi alterado silenciosamente em relação ao briefing original.

## 1. Decisões bloqueantes já resolvidas

Estas quatro decisões moldam toda a arquitetura e foram fechadas antes de prosseguir:

1. **Backoffice web mínimo** — SIM, além do mobile, mas **no mesmo repositório do app**, usando **Expo for Web** (React Native Web) em vez de uma stack de backend separada (server-rendered). Mobile continua sendo o produto principal (uso em campo por corretores/gestores); as telas administrativas pesadas (import de CSV, revisão/edição de polígono, gestão de documentos) rodam como rotas web do mesmo app Expo, reaproveitando componentes, autenticação e chamadas de API já existentes do mobile. Consequência arquitetural: o backend **não precisa** de um módulo de interface server-rendered (Jinja2/HTMX) — continua sendo puramente uma API REST consumida por um único frontend (o app Expo), rodando em duas superfícies (nativo e web). Ver decisão D2 em [03-decisoes-tecnicas.md](03-decisoes-tecnicas.md) e o backlog atualizado da Fase 5.
2. **Isolamento multi-tenant** — Row-Level Security (RLS) no PostgreSQL, não apenas filtro na aplicação. Isolamento garantido na camada de persistência mesmo se uma query esquecer o filtro de tenant.
3. **Ambiente de IA** — CPU apenas, sem GPU dedicada nos dois desenvolvedores. Modelos locais pequenos via Ollama, com abstração de `LLMProvider` para trocar de modelo/fornecedor sem tocar lógica de negócio.
4. **Offline-first** — escopo simplificado para **somente leitura**. Sem conexão, o usuário pode visualizar dados já cacheados, mas toda ação de escrita (reserva, venda, edição, upload) fica bloqueada com uma mensagem clara pedindo conexão. **Não há fila de sincronização nem resolução de conflitos no MVP** — isso elimina o maior risco técnico do projeto original.

Essas decisões estão detalhadas com opções/trade-offs em [03-decisoes-tecnicas.md](03-decisoes-tecnicas.md) (que cobre as decisões *não* bloqueantes) — as quatro acima já não têm opções em aberto.

## 2. Requisitos ausentes no briefing original

Identificados, mas **fora do escopo atual** — não são bloqueantes para começar; ficam registrados para não serem esquecidos e podem virar épicos futuros:

- Modelo de planos/limites do próprio SaaS (quantos usuários/loteamentos por plano, billing da imobiliária).
- Fluxo financeiro completo da venda: parcelamento, boleto, assinatura eletrônica de contrato.
- Cálculo e pagamento de comissão de corretores.
- Notificações (push/email/SMS) para eventos como reserva prestes a expirar ou novo lote disponível.
- Regra de negócio explícita de prazo/expiração de reserva (quanto tempo um lote fica "reservado" antes de voltar a "disponível").
- LGPD/compliance para dados pessoais de clientes (CPF, telefone, etc.) — relevante por ser um produto brasileiro.
- Política de backup/disaster recovery do banco de dados.
- CRM/funil de leads antes da reserva (captação e qualificação de interessados).
- Internacionalização/moeda — o briefing assume BRL e português; não declarado explicitamente mas implícito nos exemplos.
- Versionamento de API para lidar com apps mobile desatualizados em campo.
- SLA/uptime-alvo (não é crítico para um projeto de portfólio, mas vale declarar "não definido" em vez de ignorar).

## 3. Ambiguidades do briefing

- **Usuário multi-tenant no futuro**: o briefing pede que a arquitetura permita um usuário pertencer a mais de um tenant eventualmente, mesmo sem implementar isso agora. Resolução adotada: modelar `user` como entidade própria (não vinculada 1:1 a tenant) desde o início, com uma tabela de associação `user_tenant_membership` (papel/permissões por tenant) já na Fase 0 — mesmo que hoje só exista uma membership por usuário na prática. Isso evita uma migração dolorosa depois.
- **Estados do lote e transições**: o briefing lista estados (disponível, reservado, vendido, bloqueado, inativo) mas pede que as regras de transição sejam definidas no planejamento. Resolvidas em [04-roadmap.md](04-roadmap.md) / backlog da Fase 1 — ver tabela de transições.
- **Reserva vs. venda**: o briefing não define se reserva é temporária/expira automaticamente. Adotado para o MVP: reserva tem um responsável e um status, mas **sem expiração automática** (seria complexidade de agendamento/job desnecessária no MVP) — o gestor cancela manualmente. Registrado como simplificação deliberada.
- **RAG multi-nível (empresa → loteamento → lote → documento)**: resolvido via metadados de escopo no pgvector (`tenant_id`, `loteamento_id`, `lote_id` opcionais), não índices/coleções separadas por nível — mais simples de manter e já suficiente para filtrar por qualquer granularidade.
- **Personalização de identidade visual por tenant**: interpretado como personalização de aparência (logo, cor primária) exibida no mobile/backoffice, não personalização estrutural de campos/schema — isso mantém o modelo de dados único e evita um sistema de "custom fields" genérico (complexidade desnecessária para o escopo de portfólio).

## 4. Riscos técnicos

| Risco | Por que importa | Mitigação adotada |
|---|---|---|
| Extração de geometria a partir de imagem/planta via IA | Plantas normalmente não são georreferenciadas; não existe solução "out of the box" confiável para converter pixel → coordenada real | Passo de "rectification" assistido: usuário marca 2–3 pontos de referência conhecidos no backoffice web antes de qualquer geometria ser aceita; IA auxilia na identificação dos contornos, não na geolocalização absoluta |
| LLM local lento em CPU | Pode tornar RAG/agente impraticáveis para demonstração | Modelos pequenos (3B–8B) via Ollama + abstração `LLMProvider` para comparar/trocar sem refatorar lógica de negócio |
| RLS + pool de conexões assíncrono (FastAPI/SQLAlchemy async) | É fácil configurar RLS errado e vazar dados entre tenants, ou quebrar silenciosamente com connection pooling | Task de estudo dedicada antes da implementação (Fase 0); testes automatizados de isolamento de tenant desde a Fase 2 |
| Consultas vetoriais (pgvector) sem filtro de tenant | RLS cobre tabelas relacionais, mas uma query vetorial mal escrita pode vazar contexto de outro tenant para o RAG | Filtro de tenant explícito em toda query vetorial, como defesa em profundidade, independente da RLS |
| Complexidade simultânea (GIS + IA + mobile + offline + observabilidade) para 2 devs | Risco de dispersão, aprendizado raso em tudo | Roadmap incremental por fases (ver 04-roadmap.md), just-in-time study antes de cada fase, escopo deliberadamente simplificado onde possível (ver seção 7) |
| Bibliotecas nativas do mobile não funcionam automaticamente no Expo for Web (D2) | `expo-secure-store` e `@maplibre/maplibre-react-native`, por exemplo, não têm implementação web nativa — mapa e armazenamento de sessão precisam de uma implementação por plataforma | Abstrações por arquivo de plataforma (`.native.tsx`/`.web.tsx`) desde a Fase 3 (storage) e Fase 5 (mapa), mantendo a mesma interface/API para o resto do app — ver D2 e D8 em [03-decisoes-tecnicas.md](03-decisoes-tecnicas.md) |

## 5. Riscos de produto

- **Nunca "terminar"**: por ser projeto de portfólio + aprendizado, o risco de over-engineering contínuo é real. Mitigação: cada fase do roadmap produz uma versão funcional demonstrável, e o backlog tem critérios de aceite objetivos por task.
- **Avaliação de IA sintética**: sem usuários/dados reais, testar RAG e agentes fica artificial. Mitigação: criar um "golden set" de perguntas/respostas por tenant de teste (ver Fase 10 — Observabilidade & Evaluation) em vez de avaliar "no olho".
- **Backoffice web mal escopado**: se crescer além de "telas administrativas mínimas", vira um segundo produto e duplica esforço de frontend, mesmo compartilhando o código com o mobile via Expo for Web. Mitigação: escopo restrito a import/geometria/documentos (ver 03-decisoes-tecnicas.md).

## 6. Onde a IA é desnecessária (usar lógica determinística)

- Transições de estado do lote (disponível → reservado → vendido → bloqueado/inativo) — máquina de estados simples no backend, não IA.
- Cálculo de distância, proximidade e identificação de "lote de esquina" — consultas PostGIS determinísticas (`ST_DWithin`, `ST_Touches`, `ST_Intersects`), não LLM.
- Validação de CPF e dados cadastrais — validação determinística padrão.
- No agente de linguagem natural: a "inteligência" está em traduzir a pergunta do usuário em parâmetros de uma tool determinística (ex.: filtros SQL/PostGIS) — a busca em si nunca é "perguntar pro LLM quais lotes existem".

## 7. Complexidade deliberadamente evitada

- Microservices, filas distribuídas (Kafka), Kubernetes — YAGNI para o porte do projeto.
- Banco de vetores dedicado (Pinecone/Weaviate/etc.) — pgvector cobre a escala do projeto sem infraestrutura extra.
- CRDT completo ou fila de sincronização offline sofisticada — descartado pela decisão de offline somente-leitura (ver seção 1, item 4).
- Policy engine de permissões totalmente dinâmico/configurável desde o dia 1 — RBAC simples (papéis + tabela de permissões) é suficiente agora e pode evoluir para ABAC depois, sem exigir isso já no MVP.
- "Custom fields" genéricos por tenant — a personalização fica restrita a identidade visual (ver seção 3).
- Reserva com expiração automática/agendamento — cancelamento manual no MVP (ver seção 3).

## 8. Desafios GIS específicos

- Georreferenciar plantas/imagens não georreferenciadas exige um passo manual de calibração (pontos de referência), não é resolvível só com IA — ver seção 4.
- "Lote de esquina" e "proximidade de área verde" só funcionam se ruas e áreas verdes também existirem como geometrias no banco, não apenas os lotes — isso é um requisito de modelagem de dados a não esquecer na Fase 4 (GIS).
- SRID consistente (WGS84/4326) em todo o sistema — o mapa (MapLibre/OSM) é camada de visualização, o PostGIS é fonte de verdade; nunca inferir geometria a partir do que é mostrado no mapa.

## 9. Desafios de IA específicos

- CSV sem padrão fixo é um bom caso de uso real de LLM (mapear colunas variáveis para um schema alvo via structured output/function calling).
- Extração de geometria de planta é mais realista como combinação de OCR/visão computacional clássica (contornos) + LLM multimodal para texto (identificação, quadra, área) do que "LLM resolve tudo" — ver seção 4.
- RAG multi-nível exige metadados de escopo bem desenhados no pgvector (ver seção 3).
- Avaliação de RAG/agentes sem dataset real é difícil — mitigado com golden-set (ver seção 5 e Fase 10).

## 10. Decisões arquiteturais — ver detalhamento

As decisões arquiteturais centrais estão descritas em [02-arquitetura.md](02-arquitetura.md); as decisões técnicas não-bloqueantes (com opções e recomendação) estão em [03-decisoes-tecnicas.md](03-decisoes-tecnicas.md).
