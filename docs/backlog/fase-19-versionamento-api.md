# Fase 19 — Versionamento de API

Entrega desta fase: convenção de versionamento aplicada de fato, com um exercício real de mudança incompatível, para que um app de campo desatualizado não quebre sem aviso quando o backend evoluir. Fecha a decisão D14 (estratégia de versionamento) de `03-decisoes-tecnicas.md`. Entra depois de todo o domínio+comercial estar pronto (Fases 0–18) — só faz sentido versionar uma API já estável.

## Épico E19.1 — Fundamentos

### FASE19-EST-01-D1 / FASE19-EST-01-D2 — Estudo: estratégias de versionamento de API REST
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender as opções de versionamento (D14: path `/v1/` vs. header) e o impacto de cada uma no client (app mobile) e nos testes.
- **Conceitos a entender:** versionamento por path (`/v1/lotes`, `/v2/lotes` — rotas explícitas, fácil de documentar/testar) vs. por header (`Accept: application/vnd.lotiado.v2+json` — mais "correto" para HTTP, mas exige mais disciplina de client); como o FastAPI organiza múltiplos `APIRouter` por versão sem duplicar toda a lógica de negócio (a versão nova só precisa reimplementar o que muda, reaproveitando o serviço de aplicação por baixo); estratégia de depreciação (por quanto tempo `/v1/` continua no ar depois de `/v2/` existir).
- **Material recomendado:** documentação oficial do FastAPI sobre múltiplos routers/`APIRouter`; RFC/artigos sobre versionamento de API REST (nível conceitual).
- **Exercício prático:** criar, num projeto de exemplo isolado, dois routers (`/v1/item`, `/v2/item`) onde `/v2/` muda o formato de resposta de um campo, reaproveitando o mesmo service por baixo dos dois.
- **Critério de conclusão:** as duas versões respondem simultaneamente sem duplicar a lógica de negócio; D14 registrada como decidida.
- **Paralelizável:** Sim.

## Épico E19.2 — Aplicação

### FASE19-IMPL-01 — Estrutura de roteamento explícito por versão
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** todas as rotas existentes passam a viver explicitamente sob `/v1/`, sem quebrar nenhum client atual (app mobile já em uso).
- **Descrição:** reorganização dos `APIRouter` existentes sob um prefixo `/v1` (ou estratégia de header, conforme D14); nenhuma mudança de comportamento nesta task — é só tornar a versão explícita no contrato.
- **Pré-requisitos:** FASE19-EST-01-D1.
- **Dependências:** toda a API já existente das fases anteriores.
- **Resultado esperado:** toda rota responde sob o prefixo/versão explícita; app mobile atualizado para apontar para `/v1/` sem nenhuma outra mudança de comportamento.
- **Critérios de aceite:** suíte de testes existente passa sem alteração de asserção, só de path/header chamado.
- **Paralelizável:** Sim, com FASE19-IMPL-02 (que já pode ser desenhada em paralelo, mas só roda de fato depois desta).
- **Conhecimentos novos introduzidos:** nenhum além de FASE19-EST-01.

### FASE19-IMPL-02 — Exercício de mudança incompatível: `/v2/` convivendo com `/v1/`
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** provar na prática que um app antigo (rodando contra `/v1/`) continua funcionando quando uma mudança incompatível é introduzida em `/v2/`.
- **Descrição:** escolher um endpoint existente e mudar deliberadamente o formato de resposta de forma incompatível (ex.: renomear ou reestruturar um campo) só em `/v2/`, mantendo `/v1/` respondendo no formato antigo; ambos reaproveitam o mesmo serviço de aplicação por baixo (adaptação de formato na camada de interface, não duplicação de regra de negócio).
- **Pré-requisitos:** nenhum estudo novo além de FASE19-EST-01.
- **Dependências:** FASE19-IMPL-01.
- **Resultado esperado:** um cliente de teste simulando o app "antigo" (chamando `/v1/`) continua funcionando sem nenhuma mudança, enquanto um cliente novo (chamando `/v2/`) já usa o formato novo.
- **Critérios de aceite:** teste automatizado chama as duas versões do mesmo endpoint e valida que cada uma retorna o formato esperado da sua versão.
- **Paralelizável:** Não pode ser finalizada sem FASE19-IMPL-01.
- **Conhecimentos novos introduzidos:** convivência real de duas versões de contrato sobre o mesmo serviço de aplicação.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE19-EST-01 → FASE19-IMPL-01 (estrutura `/v1/`).
- **Dev 2:** FASE19-EST-01 → FASE19-IMPL-02 (exercício `/v2/`, depende de IMPL-01 estar pronta).
- **Pontos de sincronização:** FASE19-IMPL-02 só começa depois que a reorganização de FASE19-IMPL-01 estiver mesclada, para não haver conflito de arquivo nos routers.
