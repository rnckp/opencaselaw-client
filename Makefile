.DEFAULT_GOAL := check
.PHONY: sync format lint test check test-live build

sync:
	uv sync --locked

format:
	uv run ruff format .

lint:
	uv run ruff format --check .
	uv run ruff check .

test:
	uv run pytest

check: lint test

# Explicit opt-in: contacts the public API.
test-live:
	uv run pytest --live-api tests/opencaselaw/test_live_api.py

build:
	uv build --force-pep517
