# LotIAdo

[![CI](https://github.com/talles-coder/LotIAdo/actions/workflows/ci.yml/badge.svg)](https://github.com/talles-coder/LotIAdo/actions/workflows/ci.yml)

SaaS multitenant para gestão de loteamentos, imóveis e negociações imobiliárias. Monólito modular (FastAPI) + app Expo único (mobile + backoffice web) + PostgreSQL + IA (RAG + agentes).

Projeto de portfólio/aprendizado — ver [docs/](docs/) para a especificação completa (requisitos, arquitetura, decisões técnicas, roadmap por fase) e [CLAUDE.md](CLAUDE.md) para as regras operacionais do repositório.

## Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy async, Alembic, PostgreSQL (+PostGIS/pgvector a partir da Fase 4/7)
- **Mobile/backoffice web:** React Native + Expo (um único código-base, Expo Router)
- **Infra local:** Docker Compose (Postgres, Redis, Ollama, MinIO)

## Pré-requisitos

- **Docker + Docker Compose** — sobe Postgres/Redis/Ollama/MinIO localmente.
- **Python 3.11+** — para rodar o backend (fora de container).
- **Node.js 18+** e **npm** — para rodar o app mobile/web (Expo).
- Um dos dois, dependendo de onde você quer testar:
  - **Testar no navegador (web):** nenhum requisito extra.
  - **Testar no celular físico:** app **Expo Go** instalado ([Android](https://play.google.com/store/apps/details?id=host.exp.exponent) / [iOS](https://apps.apple.com/app/expo-go/id982107779)) e o celular na **mesma rede Wi-Fi** do computador.

Este guia cobre **web local** e **celular físico via Expo Go** (não cobre emulador Android/iOS — ver [docs/guia-rodar-android-nativo.md](docs/guia-rodar-android-nativo.md) para isso).

## Passo a passo completo

### 1. Clonar o repositório

```bash
git clone https://github.com/talles-coder/LotIAdo.git
cd LotIAdo
```

### 2. Subir a infra (Postgres, Redis, Ollama, MinIO)

```bash
make up
```

Sobe 4 containers via Docker Compose. Confirme que todos ficaram saudáveis:

```bash
docker compose ps
```

Todos devem aparecer como `Up`/`healthy`. Se a porta 5432 (Postgres), 6379 (Redis), 9000 (MinIO) ou 11434 (Ollama) já estiver em uso na sua máquina por outro serviço, ajuste `POSTGRES_PORT`/`REDIS_PORT`/`MINIO_API_PORT`/`OLLAMA_PORT` num arquivo `.env` na raiz do repo (mesmo nome usado pelo `docker-compose.yml`) antes de rodar `make up`.

**Modelos do Ollama** (necessário para os endpoints de RAG, Fase 7+) — `make up` só sobe o container vazio, os modelos não vêm pré-baixados:

```bash
docker exec lotiado-ollama ollama pull nomic-embed-text
docker exec lotiado-ollama ollama pull llama3.2
```

**Bucket do MinIO** — já é criado automaticamente pelo serviço `minio-init` do `docker-compose.yml`; não precisa de passo manual. Se quiser conferir, o console web fica em `http://localhost:9001` (login `minioadmin` / `minioadmin`).

**Tesseract OCR** (necessário para o job de extração de imagem de planta, Fase 8+) — o serviço `worker` do docker-compose (`infra/worker/Dockerfile`) já vem com o binário; só instale localmente (ex. Windows: `winget install UB-Mannheim.TesseractOCR`, adicionando a pasta de instalação ao PATH) se for chamar o pipeline de extração fora do container. O pacote de idioma "por" não vem por padrão nesse instalador — o código já cai para "eng" nesse caso, então não é bloqueante para os passos abaixo.

### 3. Configurar e subir o backend

```bash
cd backend
cp .env.example .env        # valores padrão já funcionam com `make up` acima — ajuste só se mudou portas no passo 2
pip install -r requirements.txt
cd ..
make migrate                 # aplica as migrations (alembic upgrade head) — precisa do Postgres do passo 2 já de pé
make run                     # sobe a API em 0.0.0.0:8000
```

Deixe esse terminal aberto (`make run` fica em foreground, com auto-reload). Confirme que subiu certo:

```bash
curl http://localhost:8000/health
```

Deve responder `{"status":"ok"}` (ou equivalente). O Swagger interativo fica em `http://localhost:8000/docs`.

### 4. Criar um usuário de teste para login

O banco sobe vazio (só o schema, via migrations) — sem um usuário criado, não tem como logar no app. Rode, num terminal novo (com o `.venv`/dependências do passo 3 já instaladas):

```bash
cd backend
python -m scripts.seed_user --email user@test.com --password senha123 --tenant-slug demo
```

Cria o tenant `demo` e o usuário `user@test.com` / `senha123` (role admin nesse tenant). Esse login começa **sem** loteamentos/lotes cadastrados — cadastre pela própria interface do app depois de logar, ou pela API via `/docs`.

### 5. Rodar o mobile — instalar dependências

Em outro terminal (deixe o do passo 3 rodando):

```bash
cd mobile
cp .env.example .env
npm install
```

Não inicie ainda — o valor de `EXPO_PUBLIC_API_URL` no `.env` depende de **onde** você vai testar (web ou celular físico), ajuste conforme a seção abaixo antes do `npm start`.

### 6a. Testar no navegador (web)

O padrão do `mobile/.env.example` (`EXPO_PUBLIC_API_URL=http://localhost:8000`) já funciona para web — não precisa editar nada. Suba:

```bash
npx expo start --web --port 8081
```

**Use sempre a porta 8081** — o backend só libera CORS para `localhost:8081`/`19006` (`cors_origins` em `backend/app/config.py`); rodar em outra porta quebra as chamadas à API com erro de CORS no console do navegador (não aparece erro no terminal do Expo). O Expo abre `http://localhost:8081` automaticamente no navegador padrão; se não abrir, acesse manualmente.

### 6b. Testar no celular físico (Expo Go)

1. Confirme que o celular está na **mesma rede Wi-Fi** do computador.
2. Descubra o IP local da sua máquina:
   - Windows: `ipconfig` → procure "Endereço IPv4".
   - Mac/Linux: `ifconfig` ou `ip addr`.
3. Edite `mobile/.env` e troque a URL:
   ```
   EXPO_PUBLIC_API_URL=http://<IP da sua máquina>:8000
   ```
   (ex.: `http://192.168.0.42:8000` — **não** use `localhost`, no celular ele aponta para o próprio celular, não para o seu PC.)
4. Suba o Expo:
   ```bash
   cd mobile
   npm start
   ```
5. Um QR code aparece no terminal. Abra o **app Expo Go** no celular e escaneie (Android: opção "Scan QR code" dentro do Expo Go; iOS: pela própria câmera do sistema, que reconhece o link do Expo Go).
6. O app compila o bundle JS e abre — a primeira vez demora alguns segundos.

**Se o celular não conectar:** no Windows, o Firewall costuma bloquear conexões de entrada de outros dispositivos na porta 8000 na primeira vez — quando isso acontece, o Windows normalmente pergunta se deve permitir (aceite "Redes privadas"); se não perguntou, libere manualmente em *Firewall do Windows Defender → Permitir um app*. Confirme também que o backend está com `make run` (bind em `0.0.0.0`, feito automaticamente) — `uvicorn app.main:app` sem `--host 0.0.0.0` só aceita conexões da própria máquina, mesmo com o `.env` do mobile certo.

### 7. Login

Com o app aberto (web ou celular), use o login criado no passo 4: `user@test.com` / `senha123`, tenant `demo`.

## Referência rápida: `EXPO_PUBLIC_API_URL` por ambiente

`EXPO_PUBLIC_API_URL` (em `mobile/.env`) muda dependendo de **onde** o app roda — é a causa mais comum de "o app não acha o backend". Os passos 6a/6b acima cobrem web e celular físico; para os demais ambientes (fora do escopo deste guia, ver [docs/guia-rodar-android-nativo.md](docs/guia-rodar-android-nativo.md)):

| Onde o app roda | `EXPO_PUBLIC_API_URL` |
|---|---|
| `npx expo start --web` (navegador) | `http://localhost:8000` |
| Simulador iOS | `http://localhost:8000` |
| Emulador Android | `http://10.0.2.2:8000` |
| **Celular físico (Expo Go / QR code)** | `http://<IP da sua máquina na rede local>:8000` |

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
