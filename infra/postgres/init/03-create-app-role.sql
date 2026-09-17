-- Papel de banco dedicado à aplicação (FastAPI), sem privilégios de superusuário.
--
-- O papel criado via POSTGRES_USER (ver docker-compose.yml) recebe SUPERUSER
-- pela imagem oficial do Postgres, e um superusuário sempre ignora Row-Level
-- Security, mesmo com FORCE ROW LEVEL SECURITY (ver risco D3 em
-- docs/01-analise-requisitos.md). A aplicação precisa de um papel próprio,
-- sem BYPASSRLS, para que as policies criadas nas migrations (Fase 2,
-- FASE2-IMPL-01) realmente sejam aplicadas em runtime.
--
-- `lotiado` continua sendo usado para rodar migrations (dono das tabelas,
-- precisa de privilégio para ALTER TABLE ... ENABLE/FORCE ROW LEVEL SECURITY
-- e CREATE POLICY).
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'lotiado_app') THEN
        CREATE ROLE lotiado_app WITH LOGIN PASSWORD 'lotiado_app' NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE lotiado TO lotiado_app;
GRANT USAGE ON SCHEMA public TO lotiado_app;
ALTER DEFAULT PRIVILEGES FOR ROLE lotiado IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lotiado_app;

\connect lotiado_test

GRANT CONNECT ON DATABASE lotiado_test TO lotiado_app;
GRANT USAGE ON SCHEMA public TO lotiado_app;
ALTER DEFAULT PRIVILEGES FOR ROLE lotiado IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO lotiado_app;
