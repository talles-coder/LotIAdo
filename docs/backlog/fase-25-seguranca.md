# Fase 25 — Segurança: Auditoria e Correção de Vulnerabilidades

Entrega desta fase: revisão de segurança de ponta a ponta — backend, mobile e infraestrutura de nuvem já implantada na Fase 24 — buscando tanto vulnerabilidades conhecidas (dependências, más práticas comuns) quanto decisões de design que possam ter introduzido risco ao longo do projeto, com correção do que for encontrado. É a última fase do roadmap, de propósito: só faz sentido auditar o sistema completo (incluindo o deploy real) depois que tudo mais existe. Isso não substitui as práticas de segurança já aplicadas ao longo do caminho (RLS desde a Fase 2, filtro de tenant explícito em busca vetorial desde a Fase 7, proibição explícita de texto-para-SQL na Fase 17) — é uma revisão final, não a primeira vez que segurança é considerada.

## Épico E25.1 — Fundamentos e auditoria automatizada

### FASE25-EST-01-D1 / FASE25-EST-01-D2 — Estudo: ferramentas de auditoria de segurança (SAST e dependências)
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender o que cada ferramenta de auditoria automatizada cobre (e não cobre), para não tratar "scan limpo" como "sistema seguro".
- **Conceitos a entender:** SAST (static application security testing — analisa código-fonte em busca de padrão inseguro, ex. `bandit` para Python) vs. scan de dependências vulneráveis (`pip-audit`/`safety` para Python, `npm audit` para o mobile) — são categorias diferentes de problema; falso positivo/negativo em ambas; por que scan automatizado não substitui revisão manual de lógica de autorização (isso é o Épico E25.2).
- **Material recomendado:** documentação oficial do `bandit`; documentação oficial do `pip-audit`; documentação do `npm audit`.
- **Exercício prático:** rodar `bandit` e `pip-audit` contra o próprio `backend/` e `npm audit` contra `mobile/`, e classificar manualmente 3 achados (procede / falso positivo / aceitável no contexto).
- **Critério de conclusão:** os três scans rodam localmente e o exercício de classificação está registrado (nem todo achado automatizado vira correção cega).
- **Paralelizável:** Sim.

### FASE25-IMPL-01 — Scan de dependências vulneráveis e atualização
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** nenhuma dependência com vulnerabilidade conhecida de severidade alta/crítica em produção.
- **Descrição:** `pip-audit` sobre `backend/` e `npm audit` sobre `mobile/`, atualização das dependências com vulnerabilidade conhecida (respeitando compatibilidade — não é upgrade cego de major version sem checar breaking change); scan integrado ao CI (Fase 24) para não regredir silenciosamente.
- **Pré-requisitos:** FASE25-EST-01-D1.
- **Dependências:** FASE24 (CI já existente, para integrar o scan).
- **Resultado esperado:** scan roda limpo (ou com achados documentados como aceitos conscientemente, nunca ignorados silenciosamente) e está no pipeline de CI.
- **Critérios de aceite:** dependência com vulnerabilidade crítica introduzida propositalmente num teste de sanidade é sinalizada pelo CI.
- **Paralelizável:** Sim, com FASE25-IMPL-02.
- **Conhecimentos novos introduzidos:** nenhum além de FASE25-EST-01.

### FASE25-IMPL-02 — Análise estática de código (backend e mobile)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** padrões inseguros conhecidos (ex.: uso de `eval`, SQL montado por concatenação de string, segredo hardcoded) são sinalizados automaticamente.
- **Descrição:** `bandit` sobre `backend/`; equivalente de lint de segurança no mobile (ex. regra de ESLint relevante, já que o projeto não usa uma stack com SAST dedicado para TS/RN); achados triados manualmente (nem todo achado é ação — ver exercício de FASE25-EST-01).
- **Pré-requisitos:** FASE25-EST-01-D2.
- **Dependências:** nenhuma além do código já existente.
- **Resultado esperado:** relatório de achados triados, com os que procedem corrigidos.
- **Critérios de aceite:** nenhum achado de severidade alta triado como "procede" fica sem correção ao final da fase.
- **Paralelizável:** Sim, com FASE25-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum além de FASE25-EST-01.

## Épico E25.2 — Auditoria manual de autenticação e multi-tenancy

### FASE25-IMPL-03 — Auditoria manual de autenticação, RBAC e isolamento de tenant
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** revisitar com olhar adversarial as decisões de autenticação/autorização já tomadas (D1, RLS da Fase 2), buscando brecha que os testes automatizados (Fase 23) não cobrem.
- **Descrição:** checklist manual: expiração/rotação de JWT; onde e como o token fica armazenado no mobile (`expo-secure-store` vs. alternativa web, ver D2/D8); tentativa deliberada de escalonamento de papel (usuário `corretor` tentando ação de `admin` via chamada direta à API, não só pela UI); tentativa de acessar endpoint sem `tenant_id` claro tentando vazar dado de outro tenant; revisão de todo endpoint que aceita ID de recurso vindo do client (IDOR — Insecure Direct Object Reference) sem revalidar posse/tenant.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE2 (RLS/RBAC), FASE23 (suíte de smoke multi-tenant, reaproveitada como base do teste adversarial).
- **Resultado esperado:** checklist executado com achados documentados; falhas encontradas corrigidas e cobertas por teste de regressão (adicionado à Fase 23).
- **Critérios de aceite:** tentativa de IDOR/escalonamento de papel registrada no checklist é reproduzida como teste automatizado que falha antes da correção e passa depois.
- **Paralelizável:** Sim, com FASE25-IMPL-04.
- **Conhecimentos novos introduzidos:** IDOR e escalonamento de privilégio como categorias de teste manual.

## Épico E25.3 — Auditoria de infraestrutura cloud

### FASE25-IMPL-04 — Auditoria de infraestrutura AWS (Fase 24)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** a infraestrutura implantada na Fase 24 segue princípio de menor privilégio e não expõe nada além do necessário.
- **Descrição:** checklist: IAM roles com permissão mínima necessária (não `*:*`); security groups do RDS/ECS restritos (não `0.0.0.0/0` em porta de banco); bucket S3 privado por padrão, acesso só via credencial da aplicação; criptografia em repouso (RDS, S3) e em trânsito (HTTPS/TLS) habilitada; segredos (chaves de API, senha de banco) via Secrets Manager/variável de ambiente, nunca hardcoded ou commitado no repo (checagem de histórico do git para segredo vazado).
- **Pré-requisitos:** nenhum estudo novo além do já coberto na Fase 24 (FASE24-EST-02).
- **Dependências:** FASE24 (infraestrutura já implantada).
- **Resultado esperado:** checklist executado com achados documentados e corrigidos.
- **Critérios de aceite:** nenhum recurso AWS crítico (RDS, S3, secrets) fica com acesso mais aberto do que o estritamente necessário ao final da fase.
- **Paralelizável:** Sim, com FASE25-IMPL-03.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto na Fase 24.

## Épico E25.4 — Superfície de ataque de IA e correção final

### FASE25-IMPL-05 — Revisão de superfície de ataque de IA (prompt injection e isolamento de RAG)
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** confirmar que as defesas já desenhadas nas Fases 7/9/17 (filtro de tenant explícito em busca vetorial, proibição de texto-para-SQL) resistem a tentativa deliberada de burlar via prompt.
- **Descrição:** tentativas adversariais: pedir ao agente, via prompt do usuário, para ignorar instruções e vazar dado de outro tenant/loteamento; tentar induzir a tool de relatório (Fase 17) a aceitar uma condição de filtro fora do conjunto pré-aprovado; verificar que documento de um tenant nunca aparece em resposta de outro mesmo com prompt manipulado pedindo isso explicitamente.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE7, FASE9, FASE17 (RAG, agente, tools de relatório/copiloto).
- **Resultado esperado:** tentativas adversariais documentadas, nenhuma resultando em vazamento cross-tenant; qualquer brecha encontrada é corrigida.
- **Critérios de aceite:** prompt adversarial de teste (registrado no golden-set da Fase 10) nunca retorna dado de outro tenant.
- **Paralelizável:** Sim, com FASE25-IMPL-04.
- **Conhecimentos novos introduzidos:** teste adversarial de prompt injection.

### FASE25-IMPL-06 — Correção consolidada e relatório final de auditoria
- **Tipo:** Implementação
- **Dev responsável:** Dev 1 e Dev 2
- **Objetivo:** fechar a fase com um relatório único do que foi encontrado, o que foi corrigido, e o que foi conscientemente aceito como risco (com justificativa) — não deixar achado solto sem decisão registrada.
- **Descrição:** documento curto (pode virar uma nova seção em `03-decisoes-tecnicas.md` ou um `docs/06-auditoria-seguranca.md` dedicado) listando cada achado das tasks anteriores da fase, status (corrigido/aceito/não se aplica) e link para o commit/PR de correção quando houver.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE25-IMPL-01 a 05 (todos os achados já levantados).
- **Resultado esperado:** relatório publicado em `docs/`.
- **Critérios de aceite:** todo achado de severidade alta/crítica das tasks anteriores aparece no relatório com status `corrigido` (não `aceito`, salvo justificativa explícita do usuário).
- **Paralelizável:** Não pode ser finalizada sem FASE25-IMPL-01 a 05.
- **Conhecimentos novos introduzidos:** nenhum.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE25-EST-01 → FASE25-IMPL-01 (dependências) → FASE25-IMPL-03 (auth/multi-tenancy) → FASE25-IMPL-05 (superfície de IA) → FASE25-IMPL-06 (relatório, com Dev 2).
- **Dev 2:** FASE25-EST-01 → FASE25-IMPL-02 (SAST) → FASE25-IMPL-04 (infra AWS) → FASE25-IMPL-06 (relatório, com Dev 1).
- **Pontos de sincronização:** FASE25-IMPL-06 só começa depois que todas as demais tasks da fase têm achado documentado (mesmo que a correção ainda esteja em andamento) — é o ponto de consolidação final do roadmap inteiro.
