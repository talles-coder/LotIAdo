# Fase 18 — Internacionalização & Localização

Entrega desta fase: todo texto do app extraído para arquivos de tradução (PT-BR padrão, EN como segundo idioma de prova), seletor de idioma persistido, e formatação de moeda/data por locale. Fecha a decisão D13 (biblioteca de i18n) de `03-decisoes-tecnicas.md`. Entra só depois de todo o domínio+comercial estar pronto (Fases 0–17), para não duplicar esforço de extração de texto a cada fase nova.

## Épico E18.1 — Fundamentos

### FASE18-EST-01-D1 / FASE18-EST-01-D2 — Estudo: i18n em React Native/Expo
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender extração de string, pluralização e fallback de idioma, e decidir entre `i18next`/`react-i18next` ou solução própria (decisão D13).
- **Conceitos a entender:** arquivos de tradução por idioma (chave → texto); interpolação de variável dentro de uma string traduzida (ex.: "Você tem {{n}} lotes"); pluralização (regras diferentes por idioma); fallback (se uma chave não existe no idioma ativo, cai para PT-BR); detecção do idioma do dispositivo (`expo-localization`) vs. escolha manual do usuário.
- **Material recomendado:** documentação oficial do `i18next`/`react-i18next`; documentação do `expo-localization`.
- **Exercício prático:** extrair 5-10 strings de uma tela de exemplo do próprio projeto para PT-BR/EN e alternar entre os dois manualmente.
- **Critério de conclusão:** tela de teste troca de idioma corretamente; D13 registrada como decidida.
- **Paralelizável:** Sim.

## Épico E18.2 — Extração e chaveamento

### FASE18-IMPL-01 — Extração de strings hardcoded para arquivos de tradução
- **Tipo:** Implementação
- **Dev responsável:** Dev 1 e Dev 2 (dividido por área de tela, não por dev único — é um trabalho mecânico distribuível)
- **Objetivo:** nenhum texto visível ao usuário fica hardcoded no componente; tudo vem de uma chave de tradução.
- **Descrição:** varredura de todas as telas (mobile e web, mesmo código Expo) substituindo string literal por chamada de tradução; arquivo de tradução PT-BR gerado primeiro (idioma padrão atual do produto), EN traduzido em seguida.
- **Pré-requisitos:** FASE18-EST-01-D1 (ambos os devs).
- **Dependências:** todas as telas já existentes das fases anteriores.
- **Resultado esperado:** app inteiro funcional em PT-BR sem regressão visual, arquivo EN completo (ainda não selecionável pelo usuário até FASE18-IMPL-02).
- **Critérios de aceite:** varredura automatizada (ex. lint/regra de CI simples) não encontra string literal fora de arquivo de tradução em nenhuma tela coberta.
- **Paralelizável:** Sim, dividido por módulo de tela entre os dois devs.
- **Conhecimentos novos introduzidos:** nenhum além de FASE18-EST-01.

## Épico E18.3 — Seleção de idioma e formatação

### FASE18-IMPL-02 — Seletor de idioma + formatação de moeda/data por locale
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** usuário escolhe o idioma do app (persistido entre sessões) e valores de moeda/data aparecem formatados corretamente para o locale ativo.
- **Descrição:** tela/ajuste de preferência de idioma, persistida (mesmo mecanismo de storage por plataforma já usado desde a Fase 3 — `.native.tsx`/`.web.tsx`, D2); formatação de moeda (BRL/USD) e data via `Intl.NumberFormat`/`Intl.DateTimeFormat`, não concatenação manual de string.
- **Pré-requisitos:** FASE18-EST-01-D2.
- **Dependências:** FASE18-IMPL-01.
- **Resultado esperado:** trocar o idioma na tela de preferências reflete em todo o app, incluindo formatação de valores monetários.
- **Critérios de aceite:** valor de teste em BRL formatado corretamente em PT-BR e (se moeda alternativa for exercitada) em EN; preferência de idioma sobrevive a reabrir o app.
- **Paralelizável:** Não pode ser finalizada sem FASE18-IMPL-01 estar substancialmente pronta.
- **Conhecimentos novos introduzidos:** `Intl` API para formatação por locale.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE18-EST-01 → FASE18-IMPL-01 (metade das telas) → FASE18-IMPL-02 (seletor/formatação).
- **Dev 2:** FASE18-EST-01 → FASE18-IMPL-01 (outra metade das telas).
- **Pontos de sincronização:** convenção de nomenclatura de chave de tradução (ex.: `tela.componente.acao`) combinada antes de começar a extração, para não colidir/duplicar chave entre os dois devs.
