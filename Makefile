.PHONY: dev api-dev web-dev db-up db-down migrate seed lint test

dev: db-up
	pnpm dev

api-dev:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

web-dev:
	cd apps/web && pnpm dev

db-up:
	docker compose -f infra/docker-compose.yml up -d

db-down:
	docker compose -f infra/docker-compose.yml down -v

migrate:
	cd apps/api && alembic upgrade head

seed:
	cd apps/api && python seed.py

lint:
	cd apps/api && ruff check . && mypy .
	cd apps/web && pnpm lint

test:
	cd apps/api && pytest
	cd apps/web && pnpm test:e2e
