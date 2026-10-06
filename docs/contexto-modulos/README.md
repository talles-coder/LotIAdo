# Contexto de Módulos — Mapa Vivo para Reduzir Exploração Repetida

Cada arquivo aqui é um mapa curto de um módulo (ou de um conjunto de módulos
relacionados): classes de serviço, métodos públicos com assinatura,
exceptions de domínio e o padrão de teste usado. Não substitui `docs/`
(arquitetura/decisões) nem o código — é um atalho para não repetir a mesma
exploração de código (grep/leitura de vários arquivos) toda vez que uma
tarefa nova mexe num módulo já mapeado.

## Quando criar/atualizar um arquivo aqui

- Ao iniciar uma task que exigiu explorar a fundo um módulo que ainda não
  tem arquivo aqui (ex.: mapear todos os serviços de aplicação antes de
  criar tools de agente) → crie o arquivo com o que foi levantado.
- Ao terminar uma task que mudou a superfície pública de um módulo já
  mapeado (novo método de serviço, exception nova, mudança de assinatura)
  → atualize o arquivo correspondente **antes de commitar** (ver skill
  `/commit`).
- Se o arquivo existente já está desatualizado em relação ao código, corrija
  na mesma task — não deixe a divergência para a próxima pessoa perceber.

## O que NÃO vai aqui

- Decisões de arquitetura/roadmap → `docs/02-arquitetura.md`, `docs/03-decisoes-tecnicas.md`.
- Histórico de mudanças recentes → `git log`.
- Detalhe de uma task específica já concluída → seção "Handoff" da própria
  task em `docs/backlog/fase-N-*.md` (ver convenção lá).

## Convenção de formato de cada arquivo

```
# <módulo(s)>

## Serviços de aplicação
### <NomeDoServiço> — `path/do/arquivo.py`
- método(params) -> retorno — o que faz, exceptions que levanta

## Exceptions de domínio
- `NomeDaException` (`path/exceptions.py`) — quando é levantada

## Padrão de teste
- Fixture usada, se cria entidades direto ou via HTTP, arquivo de exemplo.

## Pegadinhas / não-óbvio
- Só o que realmente surpreenderia alguém lendo o código pela primeira vez.
```

Mantenha cada arquivo curto (referência, não tutorial) — se crescer demais,
divida por módulo em vez de um arquivo monolítico.
