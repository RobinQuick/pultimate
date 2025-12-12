.PHONY: up down build test lint clean check-clean

up:
	docker compose up

down:
	docker compose down

build:
	docker compose up --build

test:
	docker compose run --rm api pytest
	# Add other service tests here as needed

lint:
	docker compose run --rm api flake8 .
	docker compose run --rm api black --check .
	docker compose run --rm api mypy .

clean:
	docker compose down -v
	rm -rf data/workspaces/*

# Helper to check for clean environment
check-clean:
	@echo "Checking environment..."
	docker compose ps
