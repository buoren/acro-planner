.PHONY: help install install-dev test test-cov lint lint-fix type-check check clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	poetry install --no-dev

install-dev: ## Install all dependencies including dev dependencies
	poetry install --with dev

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage report
	poetry run pytest --cov --cov-report=html --cov-report=term

lint: ## Run ruff linter
	poetry run ruff check .

lint-fix: ## Run ruff linter and fix issues
	poetry run ruff check --fix .

type-check: ## Run mypy type checker
	poetry run mypy .

check: lint type-check test ## Run all checks (lint, type-check, tests)

format: ## Format code with ruff
	poetry run ruff format .

clean: ## Clean up generated files
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

