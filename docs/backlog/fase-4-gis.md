# Fase 4 — GIS

Entrega desta fase: lotes com geometria real no PostGIS, mapa funcional no mobile e no backoffice (visualização, seleção, status colorido), consultas espaciais determinísticas (distância, esquina, proximidade), importação de CSV manual (mapeamento de colunas feito por humano, sem IA — isso é Fase 8).

## Épico E4.1 — Fundamentos PostGIS

### FASE4-EST-01-D1 / FASE4-EST-01-D2 — Estudo: PostGIS — tipos geográficos e consultas espaciais
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender tipos geométricos, SRID e as consultas espaciais que o produto precisa (distância, contenção, proximidade, interseção).
- **Conceitos a entender:** `GEOMETRY` vs `GEOGRAPHY`; SRID 4326 (WGS84) e por que usar um único SRID em todo o sistema; índice espacial (`GIST`); funções `ST_Distance`, `ST_DWithin`, `ST_Touches`, `ST_Intersects`, `ST_Contains`; diferença entre ponto (localização de um lote) e polígono (geometria/perímetro do lote).
- **Material recomendado:** documentação oficial do PostGIS (introdução e referência de funções); tutorial "PostGIS in Action" (capítulos introdutórios, se disponível gratuitamente) ou documentação equivalente gratuita.
- **Exercício prático:** em um banco de teste, criar uma tabela de polígonos fictícios (ex.: quadras de um bairro) e uma tabela de pontos (ex.: praças), e escrever consultas que respondam "quais polígonos estão a menos de 200m de uma praça" e "quais polígonos são vizinhos (tocam) o polígono X".
- **Critério de conclusão:** exercício responde corretamente às duas perguntas acima usando `ST_DWithin` e `ST_Touches`.
- **Paralelizável:** Sim.

### FASE4-IMPL-01 — Módulo `geo`: geometria de loteamentos e lotes
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** loteamentos e lotes passam a ter geometria real (polígono do lote, contorno do loteamento) e, quando existirem, geometrias de referência (ruas, áreas verdes) necessárias para consultas como "lote de esquina" ou "próximo da área verde".
- **Descrição:** adicionar colunas `geometry(Polygon, 4326)` em `lotes` e `loteamentos`; nova tabela `feicoes_referencia` (tipo: rua/área_verde/outro, geometria) por loteamento — sem essas feições, "esquina" e "proximidade de área verde" não têm o que consultar (risco identificado em [01-analise-requisitos.md](../01-analise-requisitos.md)); índices GIST em todas as colunas de geometria.
- **Pré-requisitos:** FASE4-EST-01-D1.
- **Dependências:** FASE1-IMPL-01 (tabela `lotes` já existe).
- **Resultado esperado:** é possível gravar e consultar a geometria de um lote e das feições de referência de um loteamento.
- **Critérios de aceite:** teste cria um polígono de lote e uma feição de rua adjacente e confirma `ST_Touches` retornando verdadeiro.
- **Paralelizável:** Sim, com FASE4-IMPL-02 (CSV), que não depende da geometria estar pronta para o mapeamento de colunas tabulares.
- **Conhecimentos novos introduzidos:** colunas geométricas, índice GIST, modelagem de feições de referência.

### FASE4-IMPL-02 — Consultas espaciais determinísticas (tools reutilizáveis)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** expor como serviços de aplicação (reutilizáveis depois pelo agente de IA na Fase 9) as consultas espaciais do briefing: distância entre lotes, lotes de esquina, proximidade de uma feição, filtro por área.
- **Descrição:** serviço `GeoQueryService` com métodos determinísticos (`distancia_entre_lotes`, `lotes_de_esquina(loteamento_id)`, `lotes_proximos_de(feicao_id, raio_m)`, `lotes_dentro_de(area_geojson)`); endpoints REST correspondentes.
- **Pré-requisitos:** FASE4-EST-01-D2.
- **Dependências:** FASE4-IMPL-01.
- **Resultado esperado:** endpoints respondem a perguntas espaciais reais do briefing (ex.: "lotes disponíveis > 200m² em esquina").
- **Critérios de aceite:** teste de integração cobre cada método com um cenário conhecido (geometrias de teste com resultado esperado calculável manualmente).
- **Paralelizável:** Não pode ser finalizada sem FASE4-IMPL-01, mas o desenho da assinatura dos métodos pode ser combinado antecipadamente.
- **Conhecimentos novos introduzidos:** consultas espaciais compostas com filtros de negócio (status do lote + critério espacial).

## Épico E4.2 — Mapa (mobile e backoffice) e importação CSV manual

### FASE4-IMPL-03 — Mapa no mobile: visualização e seleção de lotes
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** corretor visualiza o loteamento no mapa, com lotes coloridos por status, e pode tocar em um lote para ver detalhe.
- **Descrição:** tela de mapa usando `react-native-maps` (provider Google Maps) renderizando os polígonos retornados pela API (GeoJSON); cor por status; toque no polígono navega para a tela de detalhe (Fase 3). Isolar o mapa em um componente próprio (ex.: `LoteamentoMap`) com uma interface simples de props (lista de polígonos, callback de seleção) — na Fase 5 esse mesmo componente ganha uma implementação `.web.tsx` (decisão D8 em [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md)), então evitar lógica de mapa espalhada fora dele já economiza retrabalho.
- **Pré-requisitos:** nenhum estudo novo (reaproveita FASE4-EST-01 e FASE3-EST-01).
- **Dependências:** FASE4-IMPL-01, FASE3-IMPL-02.
- **Resultado esperado:** mapa interativo funcional no app.
- **Critérios de aceite:** mapa carrega os polígonos de um loteamento de teste; toque em um polígono abre o detalhe correto.
- **Paralelizável:** Sim, com FASE4-IMPL-04 (backoffice), que é uma superfície diferente.
- **Conhecimentos novos introduzidos:** renderização de GeoJSON/polígonos em `react-native-maps`, API do Google Maps.

### FASE4-IMPL-04 — Importação de CSV manual (mapeamento humano de colunas)
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** permitir importar um CSV de lotes de um loteamento, com o usuário mapeando manualmente as colunas do arquivo para os campos do sistema (sem IA nesta fase — isso é Fase 8).
- **Descrição:** endpoint que recebe um CSV, retorna os cabeçalhos encontrados; tela (no backoffice, ver Fase 5) onde o usuário associa cada coluna do CSV a um campo conhecido (identificação, quadra, área, preço); endpoint de confirmação que persiste os lotes a partir do mapeamento.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE1-IMPL-01. Não depende da Fase 5 estar pronta para o backend, mas a tela de mapeamento em si é entregue na Fase 5.
- **Resultado esperado:** backend pronto para receber CSV + mapeamento e criar lotes em lote (bulk).
- **Critérios de aceite:** CSV com colunas em ordem/nome arbitrário é importado corretamente após o mapeamento; linhas inválidas são reportadas sem abortar o restante do import.
- **Paralelizável:** Sim, com FASE4-IMPL-03.
- **Conhecimentos novos introduzidos:** parsing de CSV no backend, import em lote com relatório de erros por linha.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE4-EST-01 → FASE4-IMPL-01 (geometria) → FASE4-IMPL-03 (mapa mobile).
- **Dev 2:** FASE4-EST-01 → FASE4-IMPL-02 (consultas espaciais) → FASE4-IMPL-04 (import CSV manual, backend).
- **Pontos de sincronização:**
  1. Formato GeoJSON de resposta da API (para o mapa mobile consumir) combinado entre FASE4-IMPL-01 e FASE4-IMPL-03 antes de ambos avançarem.
  2. Esta fase pode rodar **em paralelo com a Fase 3 (mobile)** no que depende só do backend — ver [04-roadmap.md](../04-roadmap.md). FASE4-IMPL-03 especificamente depende de FASE3-IMPL-02 (tela de detalhe) já existir.
