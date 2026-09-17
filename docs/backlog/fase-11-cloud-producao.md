# Fase 11 — Cloud/Produção (AWS)

Entrega desta fase: o sistema (já funcional localmente após as fases anteriores) passa a poder ser implantado em nuvem, com CI/CD e observabilidade mínima de infraestrutura. Esta fase só começa depois que tudo funciona localmente — evita gastar tempo/créditos de cloud iterando sobre algo que ainda pode mudar (princípio geral do projeto).

## Épico E11.1 — Fundamentos de CI/CD e IaC

### FASE11-EST-01-D1 / FASE11-EST-01-D2 — Estudo: CI/CD com GitHub Actions
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** ter um pipeline que roda testes automaticamente a cada push/PR, e opcionalmente builda/publica imagens Docker.
- **Conceitos a entender:** workflows do GitHub Actions (jobs, steps, triggers); rodar testes com serviços auxiliares (Postgres/Redis) como "services" do workflow; cache de dependências para builds mais rápidos; build e push de imagem Docker para um registry.
- **Material recomendado:** documentação oficial do GitHub Actions.
- **Exercício prático:** workflow de exemplo (fora ou dentro do próprio repo) que roda `pytest` contra um Postgres de serviço do próprio Actions.
- **Critério de conclusão:** workflow de exemplo passa (verde) no GitHub.
- **Paralelizável:** Sim.

### FASE11-EST-02-D1 / FASE11-EST-02-D2 — Estudo: fundamentos de AWS para a stack do projeto
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender os serviços AWS mínimos necessários para hospedar esta stack especificamente (não um curso geral de AWS).
- **Conceitos a entender:** RDS para PostgreSQL (com extensões PostGIS/pgvector suportadas); S3 como substituto direto do MinIO (mesma interface, já abstraída desde a Fase 5 — decisão D4); ECS Fargate (ou App Runner) para rodar o container do backend sem gerenciar servidores; onde rodaria o LLM (nota: Ollama em produção na nuvem tem custo de GPU real — para o portfólio, considerar manter o `LLMProvider` local para demo e usar isso como ponto de discussão em entrevista, não necessariamente rodar Ollama na AWS); variáveis de ambiente/segredos via AWS Secrets Manager ou Parameter Store.
- **Material recomendado:** documentação oficial da AWS para RDS, S3, ECS Fargate (seções de introdução/getting started); free tier da AWS.
- **Exercício prático:** subir manualmente (via console ou CLI) uma instância RDS Postgres no free tier e conectar localmente para validar as extensões disponíveis.
- **Critério de conclusão:** consegue explicar o mapeamento direto entre cada peça local (Postgres/MinIO/backend) e seu equivalente AWS, e por que o LLM local pode continuar sendo tratado como um componente separado por ora.
- **Paralelizável:** Sim.

## Épico E11.2 — Pipeline de CI

### FASE11-IMPL-01 — Pipeline de CI: lint + testes em cada PR
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** todo PR roda automaticamente lint e a suíte de testes (backend e mobile) antes de poder ser mesclado.
- **Descrição:** workflow do GitHub Actions com serviços Postgres+PostGIS+pgvector para os testes de backend; job separado para lint/type-check do mobile (TypeScript).
- **Pré-requisitos:** FASE11-EST-01-D1.
- **Dependências:** toda a suíte de testes já existente nas fases anteriores.
- **Resultado esperado:** badge de CI verde no repositório, PRs bloqueados se os testes falharem.
- **Critérios de aceite:** um PR com um teste propositalmente quebrado é sinalizado como falho pelo CI.
- **Paralelizável:** Sim, com FASE11-IMPL-02.
- **Conhecimentos novos introduzidos:** CI real rodando a suíte de testes completa do projeto.

## Épico E11.3 — Deploy em AWS

### FASE11-IMPL-02 — Infraestrutura mínima em AWS (RDS + S3 + backend em container)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** versão do backend rodando na AWS, usando RDS (Postgres+PostGIS+pgvector) e S3 (substituindo o MinIO local) sem alterar código de negócio, graças à abstração de storage já feita na Fase 5.
- **Descrição:** provisionar RDS com as extensões habilitadas; criar bucket S3; configurar a implementação de storage já abstraída para apontar para S3 em vez de MinIO via variável de ambiente; publicar a imagem Docker do backend em um registry (ECR) e rodá-la via ECS Fargate ou App Runner.
- **Pré-requisitos:** FASE11-EST-02-D2.
- **Dependências:** FASE0-IMPL-02 (Docker), abstração de storage da Fase 5.
- **Resultado esperado:** backend acessível publicamente (ou em ambiente controlado) rodando contra infraestrutura AWS gerenciada.
- **Critérios de aceite:** trocar a variável de ambiente de storage local para S3 não exige nenhuma mudança de código, apenas configuração — validando a decisão D4; smoke test (ex.: `/health` e um endpoint de domínio) responde corretamente no ambiente AWS.
- **Paralelizável:** Sim, com FASE11-IMPL-01, desde que a imagem Docker do backend já exista (dependência leve).
- **Conhecimentos novos introduzidos:** RDS, S3, ECR, ECS Fargate/App Runner, gestão de variáveis de ambiente/segredos em produção.

### FASE11-IMPL-03 — Pipeline de CD: deploy automático após merge na main
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** merge na branch principal dispara build + deploy automático da infraestrutura de FASE11-IMPL-02.
- **Descrição:** job adicional no workflow de CI que, após os testes passarem em `main`, builda a imagem, publica no ECR e atualiza o serviço ECS/App Runner.
- **Pré-requisitos:** nenhum estudo novo além de FASE11-EST-01/02.
- **Dependências:** FASE11-IMPL-01, FASE11-IMPL-02.
- **Resultado esperado:** deploy contínuo funcional.
- **Critérios de aceite:** um merge de teste em `main` resulta em uma nova revisão do serviço rodando em produção, visível pela versão/health check.
- **Paralelizável:** Não pode ser finalizada sem FASE11-IMPL-01 e FASE11-IMPL-02.
- **Conhecimentos novos introduzidos:** CD (continuous deployment), atualização de serviço gerenciado via pipeline.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE11-EST-01/02 → FASE11-IMPL-01 (CI) → FASE11-IMPL-03 (CD).
- **Dev 2:** FASE11-EST-01/02 → FASE11-IMPL-02 (infra AWS).
- **Pontos de sincronização:** FASE11-IMPL-03 depende das duas frentes anteriores estarem prontas — é o ponto de junção final do projeto. Credenciais AWS (chaves de acesso para o pipeline) precisam ser combinadas e guardadas como secret do GitHub Actions antes de FASE11-IMPL-03 poder rodar de ponta a ponta.
