.PHONY: help dev-api dev-web test lint format clean

help:
	@echo "Available commands:"
	@echo "  make dev-api    - Start Backend API (FastAPI)"
	@echo "  make dev-web    - Start Frontend (Next.js)"
	@echo "  make test       - Run all tests (Backend)"
	@echo "  make lint       - Run linting (Ruff + Mypy)"
	@echo "  make format     - Auto-format code"

dev-api:
	cd apps/api && uvicorn main:app --reload --port 8000

dev-web:
	cd apps/web && npm run dev

test:
	cd apps/api && pytest

lint:
	cd apps/api && ruff check . && mypy .

format:
	cd apps/api && ruff check --fix . && ruff format .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
