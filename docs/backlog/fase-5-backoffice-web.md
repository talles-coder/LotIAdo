# Fase 5 — Backoffice Web Mínimo (Expo for Web)

Atualizado após decisão D2 em [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md): o backoffice **não é** um backend server-rendered separado — é o mesmo app Expo (`mobile/`) compilado também para web, com rotas específicas para as tarefas administrativas do briefing. O backend continua sendo só API REST (nenhum módulo de interface novo no backend nesta fase).

Entrega desta fase: rotas web (dentro do app Expo) para as três tarefas que não cabem bem em mobile: mapeamento de colunas do CSV (usa o backend da Fase 4), editor/revisão de polígono de lote, gestão de documentos (upload/organização — usados pela Fase 7).

## Épico E5.1 — Habilitar e estruturar o alvo web do Expo

### FASE5-EST-01-D1 / FASE5-EST-01-D2 — Estudo: Expo for Web / React Native Web
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como o Expo compila o mesmo código React Native para o navegador, e onde a paridade com o nativo quebra.
- **Conceitos a entender:** `expo start --web` e o processo de build web do Expo; quais componentes/APIs nativos não têm equivalente automático na web (ex.: `expo-secure-store`, `react-native-maps`) versus os que funcionam sem alteração (a maioria dos componentes de layout/formulário); convenção de arquivos por plataforma do Metro/Expo (`Componente.web.tsx` sobrepõe `Componente.tsx`/`Componente.native.tsx` quando o alvo é web); diferenças de navegação (Expo Router gera URLs reais na web) e de interação (hover, teclado, tamanho de tela maior).
- **Material recomendado:** documentação oficial do Expo sobre suporte a Web; documentação do Expo Router sobre comportamento específico na web.
- **Exercício prático:** pegar o app da Fase 3 (login + lista + detalhe) e rodá-lo com `expo start --web`; identificar o que quebra (ex.: `expo-secure-store` lançando erro) e corrigir criando uma versão `.web.tsx` do módulo de storage (FASE3-IMPL-01 já isolou essa interface propositalmente para este momento).
- **Critério de conclusão:** o app da Fase 3 roda no navegador com login funcional (usando `localStorage` na implementação web do storage), sem alterar as telas em si.
- **Paralelizável:** Sim.

### FASE5-IMPL-01 — Habilitar build web e resolver storage/navegação por plataforma
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** o app existente (Fases 3/4) roda no navegador sem quebrar, com sessão persistente própria da web.
- **Descrição:** habilitar o target web no `app.json`/config do Expo; criar `storage.web.tsx` (usa `localStorage`) ao lado do módulo já isolado desde FASE3-IMPL-01; validar que as rotas de autenticação e as telas de domínio (loteamentos/lotes/clientes) já funcionam na web sem alteração de lógica, só de plataforma de storage.
- **Pré-requisitos:** FASE5-EST-01-D2.
- **Dependências:** FASE3-IMPL-01, FASE3-IMPL-02.
- **Resultado esperado:** `expo start --web` sobe o app completo (Fases 3/4) funcional no navegador, exceto o mapa (tratado em FASE5-IMPL-03).
- **Critérios de aceite:** login, listagem e detalhe de lote funcionam no navegador; sessão persiste ao recarregar a página (via `localStorage`).
- **Paralelizável:** Sim, com o restante desta fase, que depende apenas do target web estar habilitado.
- **Conhecimentos novos introduzidos:** build web do Expo, arquivos de plataforma (`.web.tsx`).

## Épico E5.2 — Import CSV e editor de polígono

### FASE5-IMPL-02 — Tela web de mapeamento de colunas do CSV
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** interface para o fluxo definido em FASE4-IMPL-04 — usuário sobe o CSV, vê os cabeçalhos, associa a campos do sistema, confirma.
- **Descrição:** rota web (`app/(web)/import-csv.tsx` ou equivalente na estrutura do Expo Router) com seleção de arquivo via `expo-document-picker` (funciona em web via `<input type="file">` por baixo); após upload, busca os cabeçalhos detectados via API e renderiza os selects de mapeamento; confirmação envia o mapeamento final ao endpoint de import.
- **Pré-requisitos:** FASE5-EST-01-D1.
- **Dependências:** FASE4-IMPL-04, FASE5-IMPL-01.
- **Resultado esperado:** fluxo de import de CSV utilizável de ponta a ponta pelo navegador.
- **Critérios de aceite:** upload de um CSV de exemplo resulta nos lotes corretos após confirmação do mapeamento; erros por linha são exibidos de forma legível.
- **Paralelizável:** Sim, com FASE5-IMPL-03.
- **Conhecimentos novos introduzidos:** `expo-document-picker` no alvo web.

### FASE5-IMPL-03 — Implementação web do componente de mapa + editor/revisão de polígono
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** usuário consegue desenhar/corrigir manualmente a geometria de um lote sobre um mapa no navegador, incluindo o passo de calibração de plantas não georreferenciadas (ver risco em [01-analise-requisitos.md](../01-analise-requisitos.md)), reaproveitando o componente de mapa da Fase 4.
- **Descrição:** criar `LoteamentoMap.web.tsx` (decisão D8 em [03-decisoes-tecnicas.md](../03-decisoes-tecnicas.md)) implementando a mesma interface de props do componente nativo (FASE4-IMPL-03), usando um wrapper que reproduz a API do `react-native-maps` sobre o Google Maps JS (ex.: `@teovilla/react-native-web-maps`) — se o wrapper se mostrar instável, cair para uma implementação própria com `react-leaflet` (plano B registrado em D8); adicionar sobre esse mapa uma camada de desenho de polígono (biblioteca de desenho do Google Maps, ou do Leaflet no plano B) que salva via `PUT /lotes/{id}/geometria`; para plantas/imagens não georreferenciadas, tela auxiliar onde o usuário marca 2–3 pontos de referência conhecidos (endereço/coordenada) antes de posicionar o desenho sobre o mapa real.
- **Pré-requisitos:** nenhum estudo novo além de FASE4-EST-01 (conceitos de geometria) e FASE5-EST-01.
- **Dependências:** FASE4-IMPL-01, FASE4-IMPL-03 (interface do componente `LoteamentoMap`).
- **Resultado esperado:** é possível corrigir manualmente a geometria de qualquer lote pelo navegador, com o mesmo componente de mapa (via arquivo `.web.tsx`) usado para visualização no mobile.
- **Critérios de aceite:** polígono desenhado na tela é persistido corretamente no PostGIS (SRID 4326) e aparece de forma consistente no mapa mobile (Fase 4); o componente `LoteamentoMap` mantém a mesma interface de props nas duas plataformas.
- **Paralelizável:** Sim, com FASE5-IMPL-02.
- **Conhecimentos novos introduzidos:** wrapper de mapa para web sobre Google Maps (ou Leaflet como plano B), biblioteca de desenho de polígono, fluxo de calibração/georreferenciamento manual.

## Épico E5.3 — Gestão de documentos

### FASE5-IMPL-04 — Upload e organização de documentos por loteamento/lote
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** usuário administrativo consegue subir documentos (memorial, contratos, tabelas de preço, etc.) pelo navegador e organizá-los por loteamento/lote — base para o RAG da Fase 7.
- **Descrição:** módulo `documentos` no backend: tabela `documentos` (nome, tipo, tenant_id, loteamento_id opcional, lote_id opcional, chave no MinIO); rota web de upload (`expo-document-picker`) e listagem/filtro por loteamento/lote.
- **Pré-requisitos:** nenhum estudo novo (MinIO já coberto no estudo de Docker Compose da Fase 0; se necessário, revisar a API S3 básica usada pelo cliente Python, ex. `boto3`/`minio` SDK, como leitura rápida sem virar task de estudo formal).
- **Dependências:** FASE0-IMPL-02 (MinIO já disponível), FASE5-IMPL-01.
- **Resultado esperado:** documentos armazenados no MinIO com metadados corretos no Postgres.
- **Critérios de aceite:** upload de um PDF de teste é recuperável via URL assinada; filtro por loteamento/lote retorna os documentos corretos.
- **Paralelizável:** Sim, com FASE5-IMPL-02/03.
- **Conhecimentos novos introduzidos:** cliente S3-compatible (MinIO) a partir do Python, geração de URL assinada.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE5-EST-01 → FASE5-IMPL-02 (import CSV) → FASE5-IMPL-04 (documentos).
- **Dev 2:** FASE5-EST-01 → FASE5-IMPL-01 (habilitar web) → FASE5-IMPL-03 (mapa web/editor de polígono).
- **Pontos de sincronização:**
  1. Target web habilitado e storage web resolvidos (FASE5-IMPL-01) antes das demais telas dependerem disso — feito primeiro por Dev 2, com Dev 1 podendo começar o endpoint/tela de import em paralelo usando o app ainda só nativo.
  2. Interface de props do componente `LoteamentoMap` (definida em FASE4-IMPL-03) precisa ser respeitada por FASE5-IMPL-03 ao criar a versão `.web.tsx` — combinar qualquer ajuste necessário com quem fez a versão nativa antes de divergir.
  3. Formato do payload de geometria (`PUT /lotes/{id}/geometria`) já fixado desde a Fase 4 — reaproveitado sem mudança.
