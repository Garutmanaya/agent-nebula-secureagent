.PHONY: sync lint test

sync:
	uv sync --group dev

lint:
	uv run ruff check src tests

test:
	uv run pytest
