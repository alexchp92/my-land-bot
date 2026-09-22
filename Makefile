.PHONY: install run lint format-check test migrate

install:
	uv sync --all-groups

run:
	uv run my-land-bot

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src

test:
	uv run pytest

migrate:
	uv run alembic upgrade head
