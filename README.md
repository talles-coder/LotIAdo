# LotIAdo

SaaS multitenant para gestão de loteamentos, imóveis e negociações imobiliárias. Monólito modular (FastAPI) + app Expo único (mobile + backoffice web) + PostgreSQL + IA (RAG + agentes).

Projeto de portfólio/aprendizado — ver [docs/](docs/) para a especificação completa (requisitos, arquitetura, decisões técnicas, roadmap por fase) e [CLAUDE.md](CLAUDE.md) para as regras operacionais do repositório.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy async, Alembic, PostgreSQL (+PostGIS/pgvector a partir da Fase 4/7)
- **Mobile/backoffice web:** React Native + Expo (um único código-base, Expo Router)
- **Infra local:** Docker Compose (Postgres, Redis, Ollama, MinIO)

## Pré-requisitos

- Docker + Docker Compose
- Python 3.11+
- Node.js 18+ e um app **Expo Go** no celular (se for testar em dispositivo físico) — ou um emulador Android / simulador iOS

## Quickstart

```bash
# 1. Infra (Postgres, Redis, Ollama, MinIO)
make up

# 2. Backend
cd backend
cp .env.example .env        # ajuste se necessário
pip install -r requirements.txt
cd ..
make migrate                 # precisa das dependências instaladas (alembic)
make run                     # sobe a API em 0.0.0.0:8000 — ver "Rodando no celular" abaixo

# 3. Mobile (outro terminal)
cd mobile
cp .env.example .env         # ajuste EXPO_PUBLIC_API_URL — ver abaixo
npm install
npm start
```

Backend disponível em `http://localhost:8000` (`/docs` para o Swagger, `/health` para o healthcheck). `make help` lista todos os comandos.

## Rodando o mobile: localhost nem sempre funciona

`EXPO_PUBLIC_API_URL` (em `mobile/.env`) muda dependendo de **onde** o app roda — é a causa mais comum de "o app não acha o backend":

| Onde o app roda | `EXPO_PUBLIC_API_URL` |
|---|---|
| `npm run web` (navegador) | `http://localhost:8000` |
| Simulador iOS | `http://localhost:8000` |
| Emulador Android | `http://10.0.2.2:8000` |
| **Celular físico (Expo Go / QR code)** | `http://<IP da sua máquina na rede local>:8000` |

No celular físico, `localhost` aponta para o próprio celular, não para o seu PC — por isso precisa do IP da máquina (`ipconfig` no Windows, procure "Endereço IPv4"; `ifconfig`/`ip addr` no Mac/Linux). Celular e PC precisam estar na **mesma rede Wi-Fi**.

Além de ajustar o `.env`, o backend precisa estar escutando em todas as interfaces, não só `localhost` — é o que `make run` já faz (`--host 0.0.0.0`); rodar `uvicorn app.main:app` sem essa flag só aceita conexões da própria máquina.

**Se mesmo assim não conectar:** no Windows, o Firewall costuma bloquear conexões de entrada de outros dispositivos na porta 8000 na primeira vez — quando isso acontece, o Windows normalmente pergunta se deve permitir (aceite "Redes privadas"); se não perguntou, libere manualmente em *Firewall do Windows Defender → Permitir um app*.

## Comandos úteis (`make help`)

- `make up` / `make down` — sobe/derruba a infra
- `make reset-db` — recria os volumes do zero (banco de teste limpo)
- `make migrate` / `make migration name=...` — migrations
- `make run` — sobe a API (`0.0.0.0:8000`)
- `make test` — testes do backend

## Testes

```bash
make test
# ou, com URL de teste customizada:
cd backend && TEST_DATABASE_URL=postgresql+asyncpg://lotiado:lotiado@localhost:5432/lotiado_test pytest -v
```

## Estrutura

```
backend/   API FastAPI (módulos por domínio: tenancy, identity, loteamentos_lotes, clientes, corretores, vendas_reservas, audit)
mobile/    App Expo (mobile + backoffice web, a partir da Fase 5)
docs/      Especificação completa (requisitos, arquitetura, decisões, backlog por fase)
infra/     Scripts de inicialização dos serviços do docker-compose
```

Para navegação por task/fase, ver [docs/backlog/](docs/backlog/) e a seção "Navegação de Contexto por Tarefa" em [CLAUDE.md](CLAUDE.md).
