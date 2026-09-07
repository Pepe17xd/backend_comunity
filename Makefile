.PHONY: up down logs test migrate

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f api

test:
	pytest -q

migrate:
	alembic upgrade head
