.PHONY: install-tools install install-dev unit-test help

PROJECT_DIR = $(shell pwd)

default: help

install-tools: ## Install required utilities/tools
	@command -v pdm > /dev/null || { echo >&2 "pdm is not installed. Installing..."; pip install pdm; }
	pdm --version

install: install-tools ## Sync all required dependencies for Command Line Assistant to work
	pdm sync

install-dev: install-tools ## Sync all development dependencies
	pdm sync --dev

unit-test: ## Unit test Command Line Assistant
	@echo "Running tests..."
	@pytest tests --cov
	@echo "Tests completed."

coverage: ## Generate coverage report from unit-tests
	@coverage xml

help: ## Show available make commands
	@echo 'Usage: make <OPTIONS> ... <TARGETS>'
	@echo ''
	@echo 'Available targets are:'
	@echo ''
	@grep -E '^[ a-zA-Z0-9_.-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ''

clean: ## Clean project files
	@echo 'Cleanup project specific files...'
	@find . -name '__pycache__' -exec rm -fr {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@rm -rf .pdm-build .ruff_cache .coverage .pdm-python dist .tox
	@coverage erase
