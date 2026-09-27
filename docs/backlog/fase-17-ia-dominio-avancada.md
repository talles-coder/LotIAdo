# Fase 17 — IA de Domínio Avançada

Entrega desta fase: agente de due diligence documental, copiloto "pergunte ao loteamento" isolado por tenant, tool de relatório em linguagem natural (nunca texto-para-SQL direto), um assistente de negociação de menor prioridade, e um botão de ajuda/suporte com IA (dúvida de uso do app, não de negócio — escalona pra suporte humano quando não resolve). Nenhuma tecnologia fundamentalmente nova — extensão direta do RAG (Fase 7) e do agente LangGraph (Fase 9); por isso não há tasks de estudo novas.

## Épico E17.1 — Due diligence documental

### FASE17-IMPL-01 — Agente de due diligence: inconsistência entre documento e dado cadastrado
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** antes de uma venda ser concluída, o sistema sinaliza divergências entre o que está no documento (memorial descritivo, matrícula, licença ambiental) e o que está cadastrado no domínio/GIS.
- **Descrição:** nova tool do agente (Fase 9) que usa a busca RAG (Fase 7) sobre os documentos do lote/loteamento para extrair valores-chave (ex.: área descrita no memorial) e compara com o dado estruturado já cadastrado (ex.: área calculada do polígono GIS); diferença acima de uma tolerância configurável gera um alerta — **nunca bloqueia a venda sozinho**, é um sinal para revisão humana.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE7 (RAG), FASE9 (tools do agente), FASE4 (área do polígono GIS).
- **Resultado esperado:** para um lote de teste com documento e área propositalmente divergentes, o agente sinaliza a inconsistência.
- **Critérios de aceite:** teste com documento e cadastro consistentes não gera alerta falso; teste com divergência conhecida gera o alerta esperado.
- **Paralelizável:** Sim, com FASE17-IMPL-02.
- **Conhecimentos novos introduzidos:** extração de valor estruturado a partir de resposta do LLM sobre um documento (grounding + parsing).

## Épico E17.2 — Copiloto do loteamento

### FASE17-IMPL-02 — Copiloto "pergunte ao loteamento" isolado por tenant
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** cliente final ou corretor pergunta em linguagem natural sobre regras/infraestrutura de um loteamento específico e recebe resposta baseada só nos documentos daquele tenant/loteamento.
- **Descrição:** reaproveita o endpoint de pergunta-resposta da Fase 7 (`POST /rag/perguntar`) e o agente da Fase 9, mas com escopo obrigatoriamente restrito ao `loteamento_id` da conversa — nunca busca cross-tenant nem cross-loteamento, reforçando o filtro explícito de metadados já decidido em `01-analise-requisitos.md` (defesa em profundidade além da RLS).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE7-IMPL-03/04, FASE9.
- **Resultado esperado:** pergunta de teste sobre um loteamento retorna resposta correta citando fonte; a mesma pergunta feita com escopo de outro loteamento não vaza informação do primeiro.
- **Critérios de aceite:** teste com dois loteamentos de tenants diferentes confirma isolamento total das respostas.
- **Paralelizável:** Sim, com FASE17-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto em RAG/Agentes.

## Épico E17.3 — Relatório em linguagem natural

### FASE17-IMPL-03 — Tool de relatório sobre serviços existentes (sem texto-para-SQL)
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** corretor/gestor pergunta algo como "quantos lotes faltam pra bater a meta do trimestre" e recebe resposta cruzando dados reais do próprio tenant.
- **Descrição:** nova(s) tool(s) do agente que chamam serviços/queries de agregação **já existentes e pré-aprovados** (ex.: os mesmos usados no dashboard da Fase 16) — o LLM escolhe qual tool e quais parâmetros usar, nunca gera SQL livre contra o banco. **Nota de segurança**: texto-para-SQL direto seria capaz de bypassar RLS/isolamento de tenant mesmo com prompt cuidadoso; a tool é sempre uma função parametrizada, nunca uma via de execução de SQL arbitrário.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE9 (tools do agente), FASE16-IMPL-01 (agregações já existentes para reaproveitar).
- **Resultado esperado:** pergunta de teste sobre meta de vendas do trimestre retorna número correto.
- **Critérios de aceite:** teste garante que a tool nunca aceita uma string de SQL como parâmetro nem monta query dinâmica fora do conjunto de queries pré-aprovadas.
- **Paralelizável:** Sim, com FASE17-IMPL-01/02.
- **Conhecimentos novos introduzidos:** design de tool de relatório com superfície de ataque controlada.

## Épico E17.4 — Assistente de negociação (menor prioridade)

### FASE17-IMPL-04 — Sugestão de resposta ao corretor durante negociação
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** corretor recebe uma sugestão de resposta/argumento baseada no histórico real da conversa e no contrato daquele lote — item de menor prioridade dentro da fase, por ter qualidade mais subjetiva de avaliar.
- **Descrição:** tool que usa RAG sobre o contrato/condições comerciais do lote + histórico de conversa (Fase 12) para sugerir uma resposta; sugestão é sempre editável pelo corretor antes de enviar, nunca enviada automaticamente.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE12-IMPL-02 (histórico de conversa), FASE7 (RAG sobre contrato).
- **Resultado esperado:** sugestão de resposta gerada para uma negociação de teste.
- **Critérios de aceite:** avaliação qualitativa registrada no golden-set da Fase 10 (não critério numérico rígido, dado o caráter subjetivo).
- **Paralelizável:** Sim, com as demais tasks da fase — é a de menor prioridade, pode ficar para o fim se o tempo apertar.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto.

## Épico E17.5 — Botão de ajuda / suporte

### FASE17-IMPL-07 — Botão de ajuda com assistente de suporte (IA responde, escalona pra suporte humano)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** usuário com dúvida (não sobre o domínio de negócio, e sim sobre como usar o próprio app) tem um caminho direto de ajuda, sem precisar procurar contato de suporte solto em outro lugar.
- **Descrição:** botão de ajuda visível em qualquer tela (ex. ícone de "?" persistente); ao acionar, agente responde dúvidas comuns e pré-cadastradas sobre uso do app (reaproveitando RAG da Fase 7 sobre uma base de conhecimento própria de suporte — não a mesma base de documentos do tenant, é conteúdo genérico do produto, mesmo para todos os tenants); se a pergunta não é sobre uso do app (é dúvida de negócio) ou o agente não tem confiança na resposta, oferece escalar para o suporte humano (equipe de devs do projeto) — nesta fase, escalar = abrir um formulário simples que registra a dúvida (nome, contato, mensagem, contexto da tela onde foi acionado) para o time responder depois; **não é chat ao vivo com humano**, é ticket assíncrono.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE7 (RAG), FASE9 (agente).
- **Resultado esperado:** pergunta comum de teste (ex. "como eu cadastro um cliente novo?") é respondida pelo agente; pergunta fora do escopo de suporte de produto oferece escalar para ticket.
- **Critérios de aceite:** teste garante que o agente de suporte nunca tenta responder pergunta de negócio específica do tenant (isso é escopo do copiloto de `FASE17-IMPL-02`, não deste botão) — os dois ficam claramente separados na UI, para o usuário não confundir "ajuda sobre o app" com "pergunta sobre o meu loteamento".
- **Paralelizável:** Sim, com as demais tasks da fase.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto em RAG/Agentes.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE17-IMPL-01 (due diligence) → FASE17-IMPL-03 (relatório).
- **Dev 2:** FASE17-IMPL-02 (copiloto) → FASE17-IMPL-04 (assistente de negociação, menor prioridade — pode ser adiada) → FASE17-IMPL-07 (botão de ajuda).
- **Pontos de sincronização:** nenhum bloqueante — as tools são independentes entre si, todas plugam no mesmo agente da Fase 9. Único cuidado de design: `FASE17-IMPL-07` (ajuda sobre o app) e `FASE17-IMPL-02` (copiloto sobre o loteamento do tenant) precisam ficar visualmente distintos na UI para não confundir o usuário sobre o escopo de cada um.
