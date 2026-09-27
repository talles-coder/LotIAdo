# Fase 16 — Analytics & Precificação

Entrega desta fase: dashboard de velocidade de vendas/sazonalidade por loteamento e uma sugestão heurística de preço por comparáveis de vizinhança. Fecha a decisão D15 (biblioteca de gráficos) de `03-decisoes-tecnicas.md`.

## Épico E16.1 — Fundamentos

### FASE16-EST-01-D1 / FASE16-EST-01-D2 — Estudo: biblioteca de gráficos multiplataforma (native + web)
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** decidir e validar a biblioteca de gráfico usada no dashboard, considerando o mesmo dilema nativo+web já resolvido para mapa (D8/D10) e componentes (D9).
- **Conceitos a entender:** as opções de D15 (`victory-native`+`victory`, `react-native-gifted-charts` com fallback, ou SVG próprio via `react-native-svg`); trade-off de manter a mesma API declarativa nas duas plataformas vs. aceitar implementação distinta por plataforma (`.native.tsx`/`.web.tsx`, mesmo padrão já usado para mapa/storage).
- **Material recomendado:** documentação da(s) biblioteca(s) candidata(s); os próprios `03-decisoes-tecnicas.md` (D8/D9) como referência de critério já usado no projeto.
- **Exercício prático:** renderizar um gráfico de linha simples (dado fixo) nas duas plataformas (mobile e Expo for Web) com a opção escolhida.
- **Critério de conclusão:** gráfico de teste renderiza corretamente nas duas plataformas; D15 registrada como decidida.
- **Paralelizável:** Sim.

## Épico E16.2 — Dashboard

### FASE16-IMPL-01 — Dashboard de velocidade de vendas e sazonalidade
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** gestor vê quantos lotes foram vendidos por período e identifica padrão de sazonalidade por loteamento.
- **Descrição:** endpoint de agregação sobre vendas já existentes (Fase 1) agrupadas por período (mês); tela com gráfico de linha/barra usando a biblioteca de D15.
- **Pré-requisitos:** FASE16-EST-01-D1.
- **Dependências:** FASE1 (histórico de vendas).
- **Resultado esperado:** dashboard funcional para um loteamento de teste com dado histórico conhecido.
- **Critérios de aceite:** números do gráfico conferem com contagem manual das vendas de teste por mês.
- **Paralelizável:** Sim, com FASE16-IMPL-02.
- **Conhecimentos novos introduzidos:** nenhum além de FASE16-EST-01.

## Épico E16.3 — Precificação sugerida

### FASE16-IMPL-02 — Precificação sugerida por comparáveis de vizinhança
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** ao cadastrar/revisar o preço de um lote, o sistema sugere um valor de referência baseado em lotes próximos já vendidos.
- **Descrição:** heurística (não ML): busca lotes vendidos dentro de um raio configurável (`ST_DWithin`, mesma técnica de proximidade já usada em `01-analise-requisitos.md`, seção 6) do lote em questão, calcula preço médio por m² desses comparáveis, e sugere `preço_sugerido = área_do_lote × preço_médio_m²_vizinhança`; sugestão é só uma referência exibida ao usuário, nunca aplicada automaticamente.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE1 (histórico de vendas), FASE15-IMPL-01 (opcional — não bloqueia, mas se a camada de restrição legal já existir pode refinar a busca de comparáveis por zona).
- **Resultado esperado:** endpoint retorna preço sugerido com base nos comparáveis encontrados (ou indica que não há comparáveis suficientes).
- **Critérios de aceite:** para um conjunto de teste com vizinhança conhecida, o preço sugerido bate com o cálculo manual esperado; menos de N comparáveis (configurável) retorna aviso de "dado insuficiente" em vez de um número pouco confiável.
- **Paralelizável:** Sim, com FASE16-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto em PostGIS (Fase 4).

## Divisão de trabalho e sincronização

- **Dev 1:** FASE16-EST-01 → FASE16-IMPL-01 (dashboard).
- **Dev 2:** FASE16-EST-01 → FASE16-IMPL-02 (precificação).
- **Pontos de sincronização:** nenhum bloqueante — as duas tasks de implementação são independentes entre si.
