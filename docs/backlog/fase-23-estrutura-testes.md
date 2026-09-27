# Fase 23 — Estrutura de Testes (Unit/Integration/E2E)

Entrega desta fase: uma convenção real de testes nas duas pontas do projeto — backend (que já tem testes de integração contra banco real, mas em pasta única sem separação nem cobertura) e mobile (que hoje não tem nenhum teste). Cobre unit, integration e E2E onde cada um faz sentido, com mocks e setup de ambiente próprios.

## Levantamento de código (2026-09-27)

Confirmado por leitura direta do repositório antes de escrever esta fase:

- **Backend** (`backend/tests/`): 15 arquivos de teste numa pasta única (sem `unit/`/`integration/`), todos rodando como testes de integração contra um Postgres real (`backend/tests/conftest.py`: fixture `async_engine` cria engine async contra `TEST_DATABASE_URL`, roda `create_all`+seed de permissões, dropa tudo no teardown; fixture `client` é um `httpx.AsyncClient` com `ASGITransport` sobre a app real). `backend/pytest.ini` não define markers nem coverage (`addopts = -v --tb=short`, mais nada). Não existem testes unitários isolados (sem mock de banco) para lógica pura (ex.: máquina de estados do lote, cálculo de auditoria).
- **Mobile**: zero infraestrutura de teste — sem Jest, sem `@testing-library/react-native`, sem Detox/Maestro/Playwright, sem script `test` no `package.json`, nenhum arquivo `*.test.*`/`__tests__`.

## Épico E23.1 — Fundamentos

### FASE23-EST-01-D1 / FASE23-EST-01-D2 — Estudo: Jest + React Native Testing Library no Expo
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como configurar Jest (`jest-expo`) e testar componente/tela do mobile sem precisar de device/emulador.
- **Conceitos a entender:** preset `jest-expo` (lida com transformação de módulos nativos); `@testing-library/react-native` (render de componente, queries por texto/role, simular interação de usuário); mock de módulos nativos que não rodam em ambiente de teste (ex. `expo-secure-store`, `expo-notifications`); diferença entre teste de unidade de componente (isolado) e de integração de tela (com navegação/contexto).
- **Material recomendado:** documentação oficial do Expo sobre testing (`jest-expo`); documentação do Testing Library para React Native.
- **Exercício prático:** configurar Jest num projeto de teste Expo mínimo e testar a renderização + interação de um componente simples (ex. um botão que muda de texto ao clicar).
- **Critério de conclusão:** teste de componente de exemplo passa rodando `jest` na linha de comando.
- **Paralelizável:** Sim.

### FASE23-EST-02-D1 / FASE23-EST-02-D2 — Estudo: E2E mobile com Maestro (fallback Detox)
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** validar Maestro como framework de E2E do mobile (D16, decisão padrão) — só cair para Detox se alguma limitação real aparecer.
- **Conceitos a entender:** diferença entre teste de componente (roda em Node, sem app real) e E2E (roda o app de verdade num emulador/device); Maestro (YAML declarativo, CLI própria, sem build nativo dedicado) como ferramenta principal; Detox (build de teste específico, sincronização automática com a UI) como plano B, só se o Maestro não conseguir automatizar de forma confiável alguma interação do fluxo crítico (Épico E23.4).
- **Material recomendado:** documentação oficial do Maestro; documentação oficial do Detox (só como referência de fallback).
- **Exercício prático:** rodar um fluxo E2E mínimo (abrir o app, navegar para uma tela, verificar texto) com o Maestro.
- **Critério de conclusão:** fluxo de teste E2E de exemplo passa contra o app real num emulador com o Maestro; se não passar por limitação real da ferramenta (não por erro de configuração), documentar o motivo e repetir o exercício com Detox antes de prosseguir para `FASE23-IMPL-05`.
- **Paralelizável:** Sim.

## Épico E23.2 — Backend: unit/integration + cobertura

### FASE23-IMPL-01 — Reorganização de `backend/tests/` em `unit/` e `integration/`
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** separar testes que exercitam lógica pura (sem banco, com mock) de testes que exercitam o sistema de ponta a ponta contra Postgres real, para que os unitários rodem em milissegundos sem precisar do banco de teste no ar.
- **Descrição:** mover os 15 arquivos atuais para `backend/tests/integration/` (mantêm o comportamento atual, banco real); criar `backend/tests/unit/` com testes novos para lógica que hoje só é testada indiretamente via integração (ex.: transições válidas/inválidas da máquina de estados do lote isoladas da API, cálculo de payload de auditoria isolado do listener do SQLAlchemy) usando mock/stub em vez de sessão real; `conftest.py` correspondente de cada pasta (fixtures de banco só em `integration/conftest.py`).
- **Pré-requisitos:** nenhum estudo novo (é reorganização de código Python já dominado).
- **Dependências:** suíte de testes já existente.
- **Resultado esperado:** `pytest tests/unit` roda sem precisar do Postgres de teste no ar; `pytest tests/integration` mantém o comportamento atual.
- **Critérios de aceite:** suíte completa (`pytest`) continua verde após a reorganização, sem nenhum teste perdido/duplicado.
- **Paralelizável:** Sim, com FASE23-IMPL-02.
- **Conhecimentos novos introduzidos:** nenhum.

### FASE23-IMPL-02 — Cobertura de teste e markers no `pytest.ini`
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** saber objetivamente quanto do backend está coberto por teste, e poder rodar só unit ou só integration sob demanda.
- **Descrição:** adicionar `pytest-cov` como dependência de desenvolvimento; configurar `addopts` para gerar relatório de cobertura; declarar markers `unit`/`integration` em `pytest.ini` e marcar os testes de cada pasta (via `pyproject.toml`/`pytest.ini` + `conftest.py` de cada pasta, ou decorador explícito).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE23-IMPL-01 (pastas já separadas).
- **Resultado esperado:** `pytest -m unit` e `pytest -m integration` rodam só o subconjunto correspondente; relatório de cobertura é gerado a cada execução.
- **Critérios de aceite:** rodar `pytest -m unit` não abre nenhuma conexão com o Postgres de teste.
- **Paralelizável:** Sim, com FASE23-IMPL-01.
- **Conhecimentos novos introduzidos:** `pytest-cov`, markers do pytest.

## Épico E23.3 — Mobile: testes de unidade e integração de tela

### FASE23-IMPL-03 — Setup de Jest + testes unitários de componentes e validação
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** componentes reutilizáveis (`Field`, e as novas funções de validação da Fase 22 — CPF/CNPJ, contato) têm teste unitário próprio.
- **Descrição:** configuração de Jest (`jest-expo`) no `mobile/package.json` (script `test`); testes unitários para as funções puras de validação de documento/contato (Fase 22) — são o alvo ideal de teste unitário por não dependerem de UI; teste de componente para `Field` (renderiza label, mostra erro quando fornecido).
- **Pré-requisitos:** FASE23-EST-01-D1.
- **Dependências:** FASE22-IMPL-01/02 (funções de validação já existem para serem testadas).
- **Resultado esperado:** `npm test` roda e cobre as funções de validação com casos válidos/inválidos.
- **Critérios de aceite:** teste unitário do CPF cobre pelo menos um CPF válido e dois inválidos (dígito errado, sequência repetida tipo `111.111.111-11`).
- **Paralelizável:** Sim, com FASE23-IMPL-04.
- **Conhecimentos novos introduzidos:** nenhum além de FASE23-EST-01.

### FASE23-IMPL-04 — Testes de integração de tela com mock de API
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** telas críticas (cadastro de cliente, cadastro de corretor, login) têm teste que simula a interação do usuário sem bater numa API real.
- **Descrição:** mock da camada de chamada HTTP (`mobile/src/api/*`) via mock manual do módulo (jest `jest.mock`), sem introduzir servidor de mock adicional; teste de tela renderiza o formulário, preenche campos (incluindo casos inválidos da Fase 22), aciona submit, e verifica que a chamada de API mockada foi feita com o payload esperado (ou que o botão de salvar fica desabilitado quando inválido).
- **Pré-requisitos:** FASE23-EST-01-D2.
- **Dependências:** FASE23-IMPL-03, FASE22 (formulários já com os campos/validações novas).
- **Resultado esperado:** teste de integração da tela de cadastro de cliente cobre o caminho feliz e pelo menos um caminho de validação (CPF inválido bloqueia o submit).
- **Critérios de aceite:** teste falha propositalmente se a validação de CPF for removida (prova que o teste está de fato testando a regra, não só a existência do campo).
- **Paralelizável:** Sim, com FASE23-IMPL-03.
- **Conhecimentos novos introduzidos:** mock de módulo com Jest.

## Épico E23.4 — E2E

### FASE23-IMPL-05 — E2E mobile: fluxo crítico ponta a ponta
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** o fluxo mais crítico do app (login → criar cliente → criar reserva) é validado de ponta a ponta contra o app real, não só componente por componente.
- **Descrição:** usando o framework de D16, escrever o fluxo E2E completo rodando contra um emulador/device e um backend de teste (local); dados de teste isolados (tenant de teste dedicado a E2E, para não conflitar com dados de outros testes).
- **Pré-requisitos:** FASE23-EST-02-D1.
- **Dependências:** FASE23-IMPL-03/04 (base de teste já configurada), backend rodando localmente.
- **Resultado esperado:** fluxo E2E roda de ponta a ponta e falha claramente se qualquer etapa quebrar.
- **Critérios de aceite:** fluxo E2E passa em execução limpa (banco de teste resetado) e falha de forma legível se uma das telas do meio do caminho for propositalmente quebrada num teste de sanidade.
- **Paralelizável:** Sim, com FASE23-IMPL-06.
- **Conhecimentos novos introduzidos:** nenhum além de FASE23-EST-02.

### FASE23-IMPL-06 — Suíte de smoke test da API (backend) cobrindo fluxos críticos multi-tenant
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** existe uma suíte rodável sob demanda que valida os fluxos críticos da API de ponta a ponta (não unidade, não uma feature isolada), incluindo isolamento entre tenants.
- **Descrição:** suíte separada (`backend/tests/integration/test_smoke_e2e.py` ou similar) que simula o fluxo completo de dois tenants em paralelo (criar cliente/corretor/reserva/venda em cada um) e confirma que nenhum dado vaza entre eles — reaproveita os testes de isolamento já existentes (`test_tenant_isolation.py`, `test_rls.py`) como base, mas cobrindo o fluxo completo, não só uma entidade isolada.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE23-IMPL-01/02 (estrutura de pastas e markers já existentes — este smoke test pode ganhar seu próprio marker `smoke`).
- **Resultado esperado:** suíte roda sob demanda (`pytest -m smoke`) e cobre o fluxo crítico completo de dois tenants.
- **Critérios de aceite:** suíte falha se um vazamento de dado entre tenants for introduzido propositalmente num teste de sanidade.
- **Paralelizável:** Sim, com FASE23-IMPL-05.
- **Conhecimentos novos introduzidos:** nenhum.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE23-EST-01/02 → FASE23-IMPL-01 (reorganização backend) → FASE23-IMPL-03 (unit mobile) → FASE23-IMPL-05 (E2E mobile).
- **Dev 2:** FASE23-EST-01/02 → FASE23-IMPL-02 (cobertura/markers backend) → FASE23-IMPL-04 (integração de tela) → FASE23-IMPL-06 (smoke test API).
- **Pontos de sincronização:** convenção de marker (`unit`/`integration`/`smoke`) combinada entre os dois antes de FASE23-IMPL-02 e FASE23-IMPL-06 avançarem em paralelo.
