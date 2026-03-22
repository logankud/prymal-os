.PHONY: server test lint

server:
	uv run python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

test:
	uv run pytest

lint:
	uv run ruff check .
