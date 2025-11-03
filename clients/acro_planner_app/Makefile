.PHONY: help test test-unit test-integration analyze format clean get build-web run-web run check

# Default target
.DEFAULT_GOAL := help

# Help command
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Install dependencies
get: ## Get Flutter dependencies
	@flutter pub get

# Testing
test: test-unit ## Run all tests (widget tests only, integration tests need device)

test-unit: ## Run widget tests
	@flutter test

test-integration: ## Run integration tests (requires device)
	@echo "Running integration tests..."
	@echo "Note: This requires a device. Use 'make test-integration-macos' for desktop"
	@flutter test integration_test/app_test.dart

test-integration-macos: ## Run integration tests on macOS
	@flutter test integration_test/app_test.dart -d macos

# Code quality
analyze: ## Run Flutter analyzer
	@flutter analyze

format: ## Format code
	@dart format lib test integration_test

check: analyze test ## Run all checks (analyze and test)

# Build
build-web: ## Build for web
	@flutter build web --base-href "/acro-planner-flutter-app-733697808355/"

build-ios: ## Build for iOS (requires macOS and Xcode)
	@flutter build ios

build-android: ## Build for Android
	@flutter build apk

# Running
run: ## Run on default device
	@flutter run

run-web: ## Run on Chrome
	@flutter run -d chrome

run-ios: ## Run on iOS simulator
	@flutter run -d ios

run-android: ## Run on Android emulator
	@flutter run -d android

# Cleaning
clean: ## Clean build artifacts
	@flutter clean
	@rm -rf .dart_tool/
	@rm -rf build/