.PHONY: help test test-backend test-flutter check-backend check-flutter check deploy deploy-backend deploy-frontend clean

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[36m
RESET := \033[0m
GREEN := \033[32m

# Help command
help: ## Show this help message
	@echo "$(GREEN)Acro Planner - Master Makefile$(RESET)"
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Backend commands:$(RESET)"
	@echo "  Run 'make -C server help' for backend-specific commands"
	@echo ""
	@echo "$(GREEN)Flutter commands:$(RESET)"
	@echo "  Run 'make -C clients/acro_planner_app help' for Flutter-specific commands"

# Testing commands - run all tests locally
test: test-backend test-flutter ## Run all tests (backend and Flutter)

test-backend: ## Run backend tests
	@echo "$(GREEN)Running backend tests...$(RESET)"
	@$(MAKE) -C server test

test-flutter: ## Run Flutter tests
	@echo "$(GREEN)Running Flutter tests...$(RESET)"
	@$(MAKE) -C clients/acro_planner_app test

# Code quality checks
check: check-backend check-flutter ## Run all code quality checks

check-backend: ## Run backend checks (lint, type-check, tests)
	@echo "$(GREEN)Running backend checks...$(RESET)"
	@$(MAKE) -C server check

check-flutter: ## Run Flutter checks (analyze, tests)
	@echo "$(GREEN)Running Flutter checks...$(RESET)"
	@$(MAKE) -C clients/acro_planner_app check

# Deployment
deploy: deploy-backend deploy-frontend ## Deploy everything to production

deploy-backend: ## Deploy backend to Cloud Run
	@echo "$(GREEN)Deploying backend...$(RESET)"
	@./scripts/deploy.sh

deploy-frontend: ## Deploy Flutter web to GCS
	@echo "$(GREEN)Deploying Flutter web app...$(RESET)"
	@./scripts/deploy-frontend.sh

# Development
dev-backend: ## Run backend locally
	@echo "$(GREEN)Starting backend development server...$(RESET)"
	@cd server && poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-flutter: ## Run Flutter on Chrome
	@echo "$(GREEN)Starting Flutter development...$(RESET)"
	@$(MAKE) -C clients/acro_planner_app run-web

dev-admin: ## Run admin interface locally
	@echo "$(GREEN)Starting admin development server...$(RESET)"
	@cd admin && npm run dev

# Setup
setup: setup-backend setup-flutter ## Setup all development environments

setup-backend: ## Install backend dependencies
	@echo "$(GREEN)Setting up backend...$(RESET)"
	@$(MAKE) -C server install-dev

setup-flutter: ## Install Flutter dependencies
	@echo "$(GREEN)Setting up Flutter app...$(RESET)"
	@$(MAKE) -C clients/acro_planner_app get

# Cleaning
clean: ## Clean all build artifacts
	@echo "$(GREEN)Cleaning all build artifacts...$(RESET)"
	@$(MAKE) -C server clean 2>/dev/null || true
	@$(MAKE) -C clients/acro_planner_app clean 2>/dev/null || true
	@rm -rf htmlcov/ 2>/dev/null || true
	@rm -rf .pytest_cache/ 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(RESET)"

# Quick commands for common workflows
quick-test: ## Quick test run (no coverage)
	@echo "$(GREEN)Running quick tests...$(RESET)"
	@cd server && python3 -m pytest tests/ -v --no-cov
	@cd clients/acro_planner_app && flutter test

fix: ## Auto-fix linting issues
	@echo "$(GREEN)Auto-fixing code issues...$(RESET)"
	@cd server && ruff check . --fix
	@cd clients/acro_planner_app && dart format lib test integration_test