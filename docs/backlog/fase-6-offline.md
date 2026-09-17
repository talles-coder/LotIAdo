# Fase 6 — Offline read-cache no mobile

Escopo simplificado conforme decisão registrada em [01-analise-requisitos.md](../01-analise-requisitos.md): offline permite **somente leitura** de dados já cacheados. Toda escrita exige conexão, com aviso claro ao usuário. Sem fila de sincronização, sem resolução de conflitos.

## Épico E6.1 — Cache local e detecção de conectividade

### FASE6-EST-01-D1 / FASE6-EST-01-D2 — Estudo: cache local e conectividade em apps mobile
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como cachear dados de servidor localmente em SQLite no Expo e como detectar conectividade de forma confiável.
- **Conceitos a entender:** `expo-sqlite` para persistência local; estratégia de cache (o que cachear, quando invalidar — "stale enquanto revalida" é suficiente aqui, não é necessário nada mais sofisticado dado o escopo somente-leitura); `@react-native-community/netinfo` para detecção de conectividade; diferença entre "sem internet" e "servidor indisponível" (ambos devem bloquear escrita, mas a mensagem ao usuário pode diferir).
- **Material recomendado:** documentação oficial do `expo-sqlite`; documentação do `@react-native-community/netinfo`; documentação do TanStack Query sobre cache/`staleTime` (já em uso desde a Fase 3), que pode inclusive cobrir boa parte da necessidade de cache em memória — SQLite entra para persistir entre aberturas do app.
- **Exercício prático:** app de teste que grava uma lista em SQLite ao buscar da rede, exibe os dados do SQLite imediatamente na abertura seguinte (mesmo offline), e mostra um banner de "sem conexão" reagindo a mudanças de `NetInfo`.
- **Critério de conclusão:** exercício mostra dados cacheados offline e o banner de conectividade reage corretamente a ligar/desligar o Wi-Fi do dispositivo/emulador.
- **Paralelizável:** Sim.

### FASE6-IMPL-01 — Cache local (SQLite) dos dados do tenant ativo
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** loteamentos, lotes recentes e clientes recentes ficam disponíveis para visualização mesmo sem conexão.
- **Descrição:** ao buscar dados da API (Fase 3/4), gravar uma cópia local em SQLite; ao abrir uma tela sem conexão, ler do SQLite em vez de tentar a rede; indicar visualmente que os dados exibidos podem estar desatualizados (ex.: "última atualização: há 12 min").
- **Pré-requisitos:** FASE6-EST-01-D1.
- **Dependências:** FASE3-IMPL-02, FASE4-IMPL-03.
- **Resultado esperado:** telas de lista/detalhe/mapa funcionam offline com os últimos dados sincronizados.
- **Critérios de aceite:** com o dispositivo em modo avião, as telas já visitadas anteriormente continuam navegáveis com os dados da última sincronização, exibindo o indicador de "desatualizado".
- **Paralelizável:** Sim, com FASE6-IMPL-02.
- **Conhecimentos novos introduzidos:** persistência local SQLite, indicador de staleness de dado.

### FASE6-IMPL-02 — Bloqueio de ações de escrita quando offline
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** nenhuma ação de escrita é permitida sem conexão — nem é enfileirada, é bloqueada com uma mensagem clara (decisão do usuário, ver [01-analise-requisitos.md](../01-analise-requisitos.md)).
- **Descrição:** hook global de conectividade (`useIsOnline`, baseado em `NetInfo`); todos os botões de ação de escrita (reservar, vender, cancelar, criar cliente, upload) ficam desabilitados quando offline, com uma mensagem explicando "conecte-se à internet para editar".
- **Pré-requisitos:** FASE6-EST-01-D2.
- **Dependências:** FASE3-IMPL-03.
- **Resultado esperado:** UX consistente de bloqueio de escrita em todo o app.
- **Critérios de aceite:** em modo avião, todos os botões de escrita mapeados aparecem desabilitados com a mensagem correta; ao restaurar conexão, voltam a funcionar sem precisar reabrir o app.
- **Paralelizável:** Sim, com FASE6-IMPL-01.
- **Conhecimentos novos introduzidos:** hook de conectividade global, padrão de UI para ação bloqueada por estado do sistema.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE6-EST-01 → FASE6-IMPL-01 (cache local).
- **Dev 2:** FASE6-EST-01 → FASE6-IMPL-02 (bloqueio de escrita).
- **Pontos de sincronização:** o hook `useIsOnline` (FASE6-IMPL-02) é usado também por FASE6-IMPL-01 para decidir se busca da rede ou lê do cache — combinar a assinatura do hook antes de cada um seguir isoladamente.
