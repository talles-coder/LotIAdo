SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

.PHONY: help up down reset-db logs install migrate migration test run

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up: ## Sobe a infra (Postgres, Redis, Ollama, MinIO)
	docker compose up -d

down: ## Derruba a infra (mantém os volumes)
	docker compose down

reset-db: ## Derruba a infra e recria os volumes do zero (roda os init scripts de novo, ex: banco de teste novo)
	docker compose down -v
	docker compose up -d

logs: ## Acompanha os logs da infra
	docker compose logs -f

install: ## Instala as dependências do backend
	cd backend && pip install -r requirements.txt

migrate: ## Aplica as migrations pendentes (alembic upgrade head)
	cd backend && alembic upgrade head

migration: ## Cria uma migration nova com revision id em timestamp (uso: make migration name=create_x_table)
	cd backend && alembic revision --rev-id=$$(date +%Y%m%d%H%M%S) -m "$(name)"

test: ## Roda a suíte de testes do backend
	cd backend && pytest tests/ -v

run: ## Sobe a API em 0.0.0.0:8000 (não só localhost — necessário para o app rodar num celular físico na mesma rede)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
