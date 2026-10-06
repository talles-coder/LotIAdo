# Fase 15 — GIS Avançado & Dados Abertos

Entrega desta fase: camada opcional de restrição legal (zoneamento/APP/preservação) sobreposta ao mapa, QR code físico por lote apontando para a ficha no app, e exportação GeoJSON/CSV do loteamento inteiro. Depende só da Fase 4 (GIS base já construído com PostGIS + MapLibre).

## Épico E15.1 — Fundamentos

### FASE15-EST-01-D1 / FASE15-EST-01-D2 — Estudo: camadas de dado geoespacial público (WMS/WFS/GeoJSON) sobre MapLibre
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como consumir uma camada de dado público (ex.: zoneamento municipal, área de preservação permanente) e exibi-la como camada adicional no mapa já existente (D10 — MapLibre + OSM).
- **Conceitos a entender:** diferença entre servir uma camada como WMS (imagem renderizada pelo servidor) vs. WFS/GeoJSON (dado vetorial cru, estilizável no cliente); adicionar uma fonte de dado (`source`) e camada (`layer`) extra num mapa MapLibre já existente sem quebrar as camadas atuais; variação real de disponibilidade de dado público por município no Brasil (nem todo município publica zoneamento em formato aberto) — a feature precisa degradar bem quando o dado não existir.
- **Material recomendado:** documentação oficial do MapLibre GL JS (adicionando sources/layers); portal de dados abertos de uma prefeitura/estado à escolha como exemplo real (ex.: GeoSampa, IDE municipal disponível).
- **Exercício prático:** carregar uma camada pública real (de qualquer município com dado aberto disponível) como camada extra sobre o mapa de teste já existente do projeto.
- **Critério de conclusão:** camada pública visível sobreposta ao mapa base, sem quebrar a camada de polígonos de lote já existente.
- **Paralelizável:** Sim.

## Épico E15.2 — Overlay de restrição legal

### FASE15-IMPL-01 — Camada configurável de restrição legal por tenant
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** gestor ativa (por tenant/loteamento) uma camada de restrição legal quando houver fonte de dado disponível para aquele município — feature **best-effort**, não uma garantia de cobertura nacional.
- **Descrição:** configuração por tenant apontando a URL da fonte (WMS/WFS/GeoJSON) da camada desejada; componente de mapa (Fase 4/5) renderiza a camada quando configurada, e simplesmente não exibe nada (sem erro visível ao usuário final) quando a fonte não responde ou não está configurada.
- **Pré-requisitos:** FASE15-EST-01-D1.
- **Dependências:** FASE4 (mapa base).
- **Resultado esperado:** tenant de teste com fonte configurada mostra a camada; tenant sem fonte configurada não quebra a tela.
- **Critérios de aceite:** falha da fonte externa (timeout/404 simulado) não gera erro na tela do usuário, só ausência da camada.
- **Paralelizável:** Sim, com FASE15-IMPL-02/03.
- **Conhecimentos novos introduzidos:** consumo de camada WMS/WFS externa.

## Épico E15.3 — QR code e exportação

### FASE15-IMPL-02 — QR code por lote para placa física
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** corretor gera um QR code por lote para imprimir na placa física em campo; quem escaneia é levado direto à ficha do lote no app/portal (Fase 14).
- **Descrição:** geração de QR code (biblioteca leve, ex. `qrcode` no backend) apontando para um deep link (`lotiado://lote/{id}` com fallback web) da ficha pública do lote; endpoint que retorna a imagem do QR pronta para impressão.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE4 (lote já tem ficha própria).
- **Resultado esperado:** QR code de um lote de teste, escaneado, abre a ficha correta.
- **Critérios de aceite:** teste manual em device real confirma o deep link abrindo o app (ou a versão web como fallback se o app não estiver instalado).
- **Paralelizável:** Sim, com FASE15-IMPL-01/03.
- **Conhecimentos novos introduzidos:** geração de QR code, deep linking no Expo.

### FASE15-IMPL-03 — Exportação GeoJSON/CSV do loteamento
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** gestor exporta todos os lotes de um loteamento (geometria + atributos) para uso externo (due diligence, planilha, outro sistema GIS).
- **Descrição:** endpoint que retorna todos os lotes de um loteamento como FeatureCollection GeoJSON (geometria + atributos) ou como CSV (atributos, sem geometria, para quem só quer a planilha).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE4 (dado GIS já existe no PostGIS).
- **Resultado esperado:** exportação de um loteamento de teste abre corretamente em um visualizador GeoJSON externo (ex. geojson.io).
- **Critérios de aceite:** GeoJSON exportado é válido (schema correto) e contém todos os lotes do loteamento, sem vazar dado de outro tenant.
- **Paralelizável:** Sim, com FASE15-IMPL-01/02.
- **Conhecimentos novos introduzidos:** nenhum além de já coberto na Fase 4.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE15-EST-01 → FASE15-IMPL-01 (overlay legal) → FASE15-IMPL-03 (exportação).
- **Dev 2:** FASE15-EST-01 → FASE15-IMPL-02 (QR code).
- **Pontos de sincronização:** nenhum bloqueante — as três tasks de implementação são independentes entre si, todas dependem só da Fase 4 já pronta.
