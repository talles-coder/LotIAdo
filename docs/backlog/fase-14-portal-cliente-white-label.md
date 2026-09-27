# Fase 14 — Portal/App do Cliente Final (White-Label)

Entrega desta fase: o comprador final (não só corretor/gestor) acessa o mesmo app Expo com um papel próprio, restrito aos seus dados, para acompanhar contrato/parcelas/documentos, favoritar lotes por conta própria (upgrade do favorito interno da Fase 12), comparar lotes lado a lado, e ver a aparência do app com a marca do tenant (logo/cor). Nenhuma tecnologia fundamentalmente nova — reaproveita RBAC (Fase 2), o app único Expo (Fase 5) e os dados financeiros da Fase 13. **A coleta da identidade visual (logo, nome de exibição, cor) acontece na Fase 21** (no autocadastro do tenant e numa tela de configurações) — esta fase só aplica o que foi configurado lá.

## Épico E14.1 — Acesso do cliente final

### FASE14-IMPL-01 — Papel "cliente" no RBAC + login do cliente final
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** o comprador final tem uma conta própria, com acesso restrito apenas às suas reservas/vendas/contratos.
- **Descrição:** novo papel `cliente` no RBAC existente (Fase 2), com policy de escopo que restringe toda query a registros onde o cliente é a parte compradora; reaproveita o mesmo mecanismo de autenticação JWT já existente (Fase 0/2), sem sistema de login separado.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE2 (RBAC).
- **Resultado esperado:** usuário com papel `cliente` autentica normalmente e só vê seus próprios dados.
- **Critérios de aceite:** teste garante que um cliente autenticado não consegue acessar reserva/venda de outro cliente, mesmo sabendo o ID (retorna 403/404, não vazamento).
- **Paralelizável:** Sim, com FASE14-IMPL-04.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E14.2 — Portal do cliente

### FASE14-IMPL-02 — Telas do cliente: contrato, parcelas, documentos, favoritos
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** cliente acompanha o andamento da própria compra sem depender do corretor para cada consulta.
- **Descrição:** telas (mobile/web, mesmo app Expo) mostrando status do contrato e link de assinatura (Fase 13), parcelas com status de pagamento e link de boleto/PIX (Fase 13), documentos disponíveis (Fase 5/7); favoritos evoluem do modelo interno da Fase 12 (`Lead` ↔ `Lote`) para o cliente poder favoritar diretamente, mantendo o mesmo alerta de mudança de preço/status já implementado.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE14-IMPL-01, FASE13 (dado financeiro), FASE12-IMPL-03 (favoritos internos a evoluir).
- **Resultado esperado:** cliente de teste vê seu contrato, parcelas e documentos corretamente, e consegue favoritar um lote.
- **Critérios de aceite:** favoritar como cliente gera o mesmo alerta de mudança de preço já testado na Fase 12, agora endereçado ao próprio cliente (não só ao corretor).
- **Paralelizável:** Não pode ser finalizada sem FASE14-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum.

### FASE14-IMPL-03 — Comparador de lotes lado a lado
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** cliente escolhe 2-3 lotes disponíveis e vê uma comparação direta (m², preço/m², orientação, proximidade de amenidade).
- **Descrição:** tela que recebe uma lista de IDs de lote e monta uma tabela comparativa, reaproveitando dados já existentes no domínio/GIS (Fase 4) — sem cálculo novo além de preço/m² (divisão simples) e distância a pontos de interesse (já resolvível via PostGIS `ST_Distance`, mesma técnica de "lote de esquina"/proximidade citada em `01-analise-requisitos.md`, seção 6).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE4 (dados GIS).
- **Resultado esperado:** comparação de 2-3 lotes de teste retorna valores corretos lado a lado.
- **Critérios de aceite:** preço/m² e distância calculados batem com verificação manual para o conjunto de teste.
- **Paralelizável:** Sim, com FASE14-IMPL-02.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E14.3 — White-label

### FASE14-IMPL-04 — Theming por tenant (logo/cor primária)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** o app parece "do loteador", não do LotIAdo, quando o cliente final acessa — e não só ele: corretor/gestor do mesmo tenant também veem a marca.
- **Descrição:** **esta task só consome a configuração de marca, não a coleta** — quem produz/edita logo, nome de exibição e cor primária é `FASE14-IMPL-05`. Aqui: logo e cor primária carregados dinamicamente no tema do app (React Native Paper, D9) a partir dos dados do tenant autenticado, aplicados em toda a superfície do app.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE14-IMPL-05 (configuração de identidade visual do tenant), D9 (React Native Paper).
- **Resultado esperado:** dois tenants de teste com logo/cor diferentes (configurados via FASE14-IMPL-05) mostram o app com aparência distinta.
- **Critérios de aceite:** trocar de tenant (logout/login com outro cliente) reflete a marca correta sem exigir novo build do app; tenant que não configurou marca própria usa o visual padrão do LotIAdo (fallback, não tela quebrada).
- **Paralelizável:** Não pode ser finalizada sem FASE14-IMPL-05.
- **Conhecimentos novos introduzidos:** tema dinâmico em tempo de execução com React Native Paper.

### FASE14-IMPL-05 — Tela de configuração de identidade visual do tenant (logo, nome de exibição, cor)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** a imobiliária consegue definir e depois trocar seu logo, nome de exibição e cor primária, sem depender de um dev alterar dado manualmente.
- **Descrição:** tela de configurações (acessível pelo papel `admin` do tenant) com upload de logo (reaproveita storage já abstraído, MinIO/S3, Fase 5), campo de nome de exibição (pode diferir da razão social) e seletor de cor primária (paleta restrita, não color picker livre, para evitar combinação ilegível — ver `docs/design/lovable-mapeamento.md` para os tokens de referência); mesma tela é reaproveitada no fluxo de autocadastro (Fase 21), como etapa opcional (`pular por agora` disponível, com fallback visual padrão do LotIAdo).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE2 (dado de tenant), FASE5 (storage), D9 (React Native Paper).
- **Resultado esperado:** admin do tenant altera logo/nome/cor e a mudança reflete imediatamente (sem novo build) para todos os usuários daquele tenant.
- **Critérios de aceite:** upload de logo em formato/tamanho inválido é rejeitado com mensagem clara (não erro genérico); cor escolhida nunca deixa texto ilegível (contraste mínimo validado, não é escolha 100% livre).
- **Paralelizável:** Sim, com FASE14-IMPL-01.
- **Conhecimentos novos introduzidos:** validação de contraste de cor (WCAG, nível básico).

## Divisão de trabalho e sincronização

- **Dev 1:** FASE14-IMPL-01 (RBAC cliente) → FASE14-IMPL-03 (comparador).
- **Dev 2:** FASE14-IMPL-05 (configuração de marca, pode começar em paralelo) → FASE14-IMPL-04 (aplica o theming) → FASE14-IMPL-02 (telas do cliente, depende do RBAC do Dev 1).
- **Pontos de sincronização:** policy de escopo do papel `cliente` (o que exatamente ele pode ler) combinada antes de FASE14-IMPL-02 começar a consumir os endpoints; formato dos dados de marca (campos de `FASE14-IMPL-05`) combinado antes de `FASE14-IMPL-04` consumi-los.
