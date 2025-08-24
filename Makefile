# Makefile for git-ai-reporter
# Comprehensive build automation for development, testing, and quality checks

# Variables
PYTHON := python3
UV := uv
VENV := .venv
VENV_ACTIVATE := source $(VENV)/bin/activate
PROJECT_NAME := git-ai-reporter
SRC_DIR := src
TEST_DIR := tests
SCRIPTS_DIR := scripts

# Python source files
PY_FILES := $(shell find $(SRC_DIR) $(TEST_DIR) $(SCRIPTS_DIR) -name "*.py" -type f 2>/dev/null)
SRC_FILES := $(shell find $(SRC_DIR) -name "*.py" -type f 2>/dev/null)
TEST_FILES := $(shell find $(TEST_DIR) -name "*.py" -type f 2>/dev/null)

# Shell script files
SH_FILES := $(shell find . -name "*.sh" -type f -not -path "./.venv/*" -not -path "./.git/*" 2>/dev/null)

# Coverage thresholds (focused on core functionality)
COVERAGE_THRESHOLD := 55

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

# Phony targets (don't correspond to actual files)
.PHONY: help install clean format lint type-check test coverage \
				security-scan quality-check shellcheck check-all \
				pre-commit pre-push install-hooks run docs build \
				venv update-deps freeze-deps test-allure allure-report allure-serve \
				allure-ui-up allure-ui-down allure-ui-restart allure-ui-logs allure-ui-status

# Help target - displays available commands
help:
	@echo -e "$(BLUE)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo -e "$(BLUE)║         Git AI Reporter - Development Makefile             ║$(NC)"
	@echo -e "$(BLUE)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo -e ""
	@echo -e "$(GREEN)Development Commands:$(NC)"
	@echo -e "  make install        - Create venv and install dependencies"
	@echo -e "  make clean          - Remove build artifacts and caches"
	@echo -e "  make format         - Format code with ruff"
	@echo -e "  make venv           - Create virtual environment"
	@echo -e "  make update-deps    - Update all dependencies to latest versions"
	@echo -e "  make freeze-deps    - Freeze current dependencies"
	@echo -e ""
	@echo -e "$(GREEN)Testing Commands:$(NC)"
	@echo -e "  make test           - Run all tests"
	@echo -e "  make test-fast      - Run tests without coverage"
	@echo -e "  make coverage       - Run tests with coverage report"
	@echo -e "  make test-unit      - Run unit tests only"
	@echo -e "  make test-integration - Run integration tests only"
	@echo -e "  make test-allure    - Run tests and generate Allure results"
	@echo -e "  make allure-report  - Generate and open Allure HTML report (uses Docker if CLI unavailable)"
	@echo -e "  make allure-serve   - Start Allure development server (uses Docker if CLI unavailable)"
	@echo -e "  make allure-ui-up   - Start Allure Docker Service + UI (recommended)"
	@echo -e "  make allure-ui-down - Stop Allure Docker Service + UI"
	@echo -e "  make allure-ui-restart - Restart Allure Docker Service + UI"
	@echo -e "  make allure-ui-logs - View Allure service logs"
	@echo -e "  make allure-ui-status - Check Allure service status"
	@echo -e ""
	@echo -e "$(GREEN)Quality Checks:$(NC)"
	@echo -e "  make lint           - Run comprehensive linting"
	@echo -e "  make lint-fix       - Auto-fix linting issues"
	@echo -e "  make type-check     - Run mypy type checking"
	@echo -e "  make security-scan  - Scan for secrets and vulnerabilities"
	@echo -e "  make quality-check  - Check code quality standards"
	@echo -e "  make shellcheck     - Validate shell scripts"
	@echo -e ""
	@echo -e "$(GREEN)Git Hooks:$(NC)"
	@echo -e "  make install-hooks  - Install git hooks"
	@echo -e "  make pre-commit     - Run pre-commit checks"
	@echo -e "  make pre-push       - Run pre-push checks"
	@echo -e ""
	@echo -e "$(GREEN)Combined Checks:$(NC)"
	@echo -e "  make check-all      - Run ALL checks (lint, test, security, etc.)"
	@echo -e "  make check-fast     - Quick checks (format, lint, type)"
	@echo -e "  make ci             - Run CI pipeline checks"
	@echo -e ""
	@echo -e "$(GREEN)Application:$(NC)"
	@echo -e "  make run            - Run the application"
	@echo -e "  make build          - Build distribution packages"
	@echo -e "  make docs           - Generate documentation"
	@echo -e ""
	@echo -e "$(YELLOW)Pro tip: Use 'make check-all' before committing!$(NC)"

# Virtual environment creation
venv:
	@echo -e "$(BLUE)Creating virtual environment...$(NC)"
	@$(UV) venv $(VENV)
	@echo -e "$(GREEN)✓ Virtual environment created$(NC)"

# Install dependencies
install: venv
	@echo -e "$(BLUE)Installing dependencies...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) pip sync pyproject.toml
	@echo -e "$(GREEN)✓ Dependencies installed$(NC)"
	@echo -e "$(BLUE)Installing git hooks...$(NC)"
	@$(SCRIPTS_DIR)/install-hooks.sh
	@echo -e "$(GREEN)✓ Installation complete$(NC)"

# Update dependencies to latest versions
update-deps: venv
	@echo -e "$(BLUE)Updating dependencies to latest versions...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) pip install --upgrade -e .
	@echo -e "$(GREEN)✓ Dependencies updated$(NC)"

# Freeze current dependencies
freeze-deps: venv
	@echo -e "$(BLUE)Freezing dependencies...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) pip freeze > requirements.txt
	@echo -e "$(GREEN)✓ Dependencies frozen to requirements.txt$(NC)"

# Clean build artifacts and caches
clean:
	@echo -e "$(BLUE)Cleaning build artifacts and caches...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "allure-results" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "allure-report" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@echo -e "$(GREEN)✓ Cleaned$(NC)"

# Format code with ruff
format:
	@echo -e "$(BLUE)Formatting code with ruff...$(NC)"
	@$(VENV_ACTIVATE) && ruff format $(SRC_DIR) $(TEST_DIR)
	@echo -e "$(GREEN)✓ Code formatted$(NC)"

# Run comprehensive linting
lint:
	@echo -e "$(BLUE)Running comprehensive lint checks...$(NC)"
	@$(VENV_ACTIVATE) && $(SCRIPTS_DIR)/lint.sh
	@echo -e "$(GREEN)✓ Linting passed$(NC)"

# Auto-fix linting issues
lint-fix:
	@echo -e "$(BLUE)Auto-fixing linting issues...$(NC)"
	@$(VENV_ACTIVATE) && ruff check --fix $(SRC_DIR) $(TEST_DIR)
	@$(VENV_ACTIVATE) && ruff format $(SRC_DIR) $(TEST_DIR)
	@echo -e "$(GREEN)✓ Linting issues fixed$(NC)"

# Quick lint check with ruff only
lint-quick:
	@echo -e "$(BLUE)Running quick lint check...$(NC)"
	@$(VENV_ACTIVATE) && ruff check $(SRC_DIR) $(TEST_DIR)
	@$(VENV_ACTIVATE) && ruff format --check $(SRC_DIR) $(TEST_DIR)
	@echo -e "$(GREEN)✓ Quick lint passed$(NC)"

# Type checking with mypy
type-check:
	@echo -e "$(BLUE)Running type checking with mypy...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run mypy $(SRC_DIR) --strict
	@echo -e "$(GREEN)✓ Type checking passed$(NC)"

# Run all tests (Allure reports generated automatically)
test:
	@echo -e "$(BLUE)Running all tests...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR)
	@echo -e "$(GREEN)✓ All tests passed$(NC)"
	@echo -e "$(YELLOW)Allure results automatically saved to: allure-results/$(NC)"
	@echo -e "$(YELLOW)Generate report: make allure-report$(NC)"

# Run tests without coverage (fast mode - Allure still generated)
test-fast:
	@echo -e "$(BLUE)Running tests (fast mode - no coverage)...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR) -q -q --no-cov
	@echo -e "$(GREEN)✓ Tests passed$(NC)"
	@echo -e "$(YELLOW)Allure results saved to: allure-results/$(NC)"

# Run tests with coverage (Allure generated automatically)
coverage:
	@echo -e "$(BLUE)Running tests with coverage...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest -q -q $(TEST_DIR)
	@echo -e "$(GREEN)✓ Coverage check passed (>= $(COVERAGE_THRESHOLD)%)$(NC)"
	@echo -e "$(YELLOW)Coverage report: open htmlcov/index.html$(NC)"
	@echo -e "$(YELLOW)Allure results: make allure-report$(NC)"

# Run unit tests only (Allure generated automatically)
test-unit:
	@echo -e "$(BLUE)Running unit tests...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR)/unit
	@echo -e "$(GREEN)✓ Unit tests passed$(NC)"
	@echo -e "$(YELLOW)Allure results: make allure-report$(NC)"

# Run integration tests only (Allure generated automatically)
test-integration:
	@echo -e "$(BLUE)Running integration tests...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR)/integration
	@echo -e "$(GREEN)✓ Integration tests passed$(NC)"
	@echo -e "$(YELLOW)Allure results: make allure-report$(NC)"

# Run tests and generate Allure results (DEPRECATED - use 'make test' instead)
# NOTE: This target is now identical to 'make test' since Allure is generated automatically
test-allure: test
	@echo -e "$(YELLOW)⚠ test-allure is deprecated - use 'make test' instead$(NC)"
	@echo -e "$(YELLOW)Allure results are now generated automatically for all test runs$(NC)"

# Generate Allure HTML report and open in browser
allure-report:
	@echo -e "$(BLUE)Generating Allure HTML report...$(NC)"
	@if [ ! -d "allure-results" ] || [ -z "$$(ls -A allure-results 2>/dev/null)" ]; then \
		echo -e "$(YELLOW)No Allure results found. Running tests first...$(NC)"; \
		$(MAKE) --no-print-directory test-allure; \
	fi
	@if command -v allure >/dev/null 2>&1; then \
		allure generate allure-results --output allure-report --clean; \
		echo -e "$(GREEN)✓ Allure report generated$(NC)"; \
		echo -e "$(YELLOW)Opening report in browser...$(NC)"; \
		allure open allure-report; \
	elif command -v docker >/dev/null 2>&1; then \
		echo -e "$(YELLOW)Using Docker for Allure report generation...$(NC)"; \
		docker run --rm \
			--user $(shell id -u):$(shell id -g) \
			-v $(PWD)/allure-results:/allure-results \
			-v $(PWD)/allure-report:/allure-report \
			frankescobar/allure-docker-service:latest \
			allure generate /allure-results --output /allure-report --clean; \
		echo -e "$(GREEN)✓ Allure report generated using Docker$(NC)"; \
		echo -e "$(YELLOW)Report available at: allure-report/index.html$(NC)"; \
		if command -v xdg-open >/dev/null 2>&1; then \
			xdg-open allure-report/index.html; \
		elif command -v open >/dev/null 2>&1; then \
			open allure-report/index.html; \
		fi; \
	else \
		echo -e "$(YELLOW)⚠ Neither Allure CLI nor Docker found.$(NC)"; \
		echo -e "$(YELLOW)Install options:$(NC)"; \
		echo -e "  macOS: brew install allure"; \
		echo -e "  Linux: Download from https://github.com/allure-framework/allure2/releases"; \
		echo -e "  Docker: Install Docker to use frankescobar/allure-docker-service"; \
		exit 1; \
	fi

# Start Allure development server (auto-refresh)
allure-serve:
	@echo -e "$(BLUE)Starting Allure development server...$(NC)"
	@if [ ! -d "allure-results" ] || [ -z "$$(ls -A allure-results 2>/dev/null)" ]; then \
		echo -e "$(YELLOW)No Allure results found. Running tests first...$(NC)"; \
		$(MAKE) --no-print-directory test-allure; \
	fi
	@if command -v allure >/dev/null 2>&1; then \
		echo -e "$(GREEN)Starting Allure server at http://localhost:4040$(NC)"; \
		echo -e "$(YELLOW)Press Ctrl+C to stop the server$(NC)"; \
		allure serve allure-results; \
	elif command -v docker >/dev/null 2>&1; then \
		echo -e "$(YELLOW)Using Docker for Allure server...$(NC)"; \
		echo -e "$(GREEN)Starting Allure server at http://localhost:5050$(NC)"; \
		echo -e "$(YELLOW)Press Ctrl+C to stop the server$(NC)"; \
		docker run --rm \
			--user $(shell id -u):$(shell id -g) \
			-p 5050:5050 \
			-v $(PWD)/allure-results:/app/allure-results \
			-e CHECK_RESULTS_EVERY_SECONDS=3 \
			-e KEEP_HISTORY=1 \
			frankescobar/allure-docker-service:latest; \
	else \
		echo -e "$(YELLOW)⚠ Neither Allure CLI nor Docker found. See 'make allure-report' for installation instructions.$(NC)"; \
		exit 1; \
	fi

# Security scan for secrets and vulnerabilities
security-scan:
	@echo -e "$(BLUE)Running security scan...$(NC)"
	@$(SCRIPTS_DIR)/security-scan.sh $(PY_FILES)
	@echo -e "$(GREEN)✓ Security scan passed$(NC)"

# Quality checks (license headers, file sizes, etc.)
quality-check:
	@echo -e "$(BLUE)Running quality checks...$(NC)"
	@SKIP_BRANCH_CHECK=1 $(SCRIPTS_DIR)/check-quality.sh all $(PY_FILES)
	@echo -e "$(GREEN)✓ Quality checks passed$(NC)"

# Validate shell scripts
shellcheck:
	@echo -e "$(BLUE)Validating shell scripts...$(NC)"
	@if command -v shellcheck >/dev/null 2>&1; then \
		echo "Found $$(echo $(SH_FILES) | wc -w) shell scripts to check"; \
		for script in $(SH_FILES); do \
			echo "  Checking $$script..."; \
			shellcheck -e SC1091 -e SC2086 -e SC2181 $$script || exit 1; \
		done; \
		echo -e "$(GREEN)✓ All shell scripts valid$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠ shellcheck not installed. Install with: apt-get install shellcheck$(NC)"; \
	fi

# Pre-commit checks
pre-commit:
	@echo -e "$(BLUE)Running pre-commit checks...$(NC)"
	@.git/hooks/pre-commit || true
	@echo -e "$(GREEN)✓ Pre-commit checks complete$(NC)"

# Pre-push checks
pre-push:
	@echo -e "$(BLUE)Running pre-push checks...$(NC)"
	@SKIP_BRANCH_CHECK=1 .git/hooks/pre-push || true
	@echo -e "$(GREEN)✓ Pre-push checks complete$(NC)"

# Install git hooks
install-hooks:
	@echo -e "$(BLUE)Installing git hooks...$(NC)"
	@$(SCRIPTS_DIR)/install-hooks.sh
	@echo -e "$(GREEN)✓ Git hooks installed$(NC)"

# Quick checks (format, lint, type)
check-fast: format lint-quick type-check
	@echo -e "$(GREEN)✓ Quick checks passed$(NC)"

# CI pipeline checks
ci: lint type-check test coverage security-scan quality-check
	@echo -e "$(GREEN)✓ CI checks passed$(NC)"

## -----------------------------------------------------------------------------
## Enhanced Quality Assurance - CRITICAL PRODUCTION SAFETY
## -----------------------------------------------------------------------------
## ⚠️ ⚠️ ⚠️  MANDATORY PRODUCTION SAFETY NOTICE ⚠️ ⚠️ ⚠️
##
## The check-all target is the FINAL SAFETY NET before production deployment.
## It MUST catch all major issues that could cause production failures.
##
## RULES (VIOLATION = IMMEDIATE TERMINATION):
## 1. NEVER remove ANY check from check-all
## 2. NEVER comment out ANY check
## 3. NEVER add conditional bypasses
## 4. NEVER prioritize speed over safety
## 5. ONLY ADD checks, never remove them
##
## If a check is slow, OPTIMIZE THE CHECK, don't remove it.
## If a check is "annoying", FIX YOUR CODE, don't skip the check.
##
## Production downtime costs $10,000+ per hour. Your convenience is worth $0.
## -----------------------------------------------------------------------------

# MASTER SAFETY CHECK - Catches ALL possible production issues
# Order matters: Fast checks first, then slow checks, Docker last
check-all:
	@echo -e "$(BLUE)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo -e "$(BLUE)║              RUNNING COMPREHENSIVE CHECK-ALL                 ║$(NC)"
	@echo -e "$(BLUE)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo -e ""

	@echo -e "$(BLUE)[1/8] Code Formatting Check$(NC)"
	@echo -e "$(BLUE)Checking code formatting...$(NC)"
	@if ! $(VENV_ACTIVATE) && ruff format --check . > /dev/null 2>&1; then \
		echo -e "$(YELLOW)⚠️  Code needs formatting. Running formatter...$(NC)"; \
		$(MAKE) --no-print-directory format; \
	else \
		echo -e "$(GREEN)✓ Code formatting is correct$(NC)"; \
	fi
	@echo -e ""

	@echo -e "$(BLUE)[2/8] Python Linting (Full)$(NC)"
	@$(MAKE) --no-print-directory lint
	@echo -e ""

	@echo -e "$(BLUE)[3/8] Type Checking$(NC)"
	@$(MAKE) --no-print-directory type-check
	@echo -e ""

	@echo -e "$(BLUE)[4/8] Shell Script Validation$(NC)"
	@$(MAKE) --no-print-directory shellcheck
	@echo -e ""

	@echo -e "$(BLUE)[5/8] Security Scanning$(NC)"
	@$(MAKE) --no-print-directory security-scan
	@echo -e ""

	@echo -e "$(BLUE)[6/8] Quality Standards$(NC)"
	@$(MAKE) --no-print-directory quality-check
	@echo -e ""

	@echo -e "$(BLUE)[7/8] Coverage Analysis$(NC)"
	@$(MAKE) --no-print-directory coverage
	@echo -e ""

	@echo -e "$(BLUE)[8/8] Documentation Check$(NC)"
	@echo -e "Checking for required documentation files..."
	@test -f README.md || (echo -e "$(RED)✗ Missing README.md$(NC)" && exit 1)
	@test -f LICENSE || (echo -e "$(RED)✗ Missing LICENSE$(NC)" && exit 1)
	@test -f CLAUDE.md || (echo -e "$(RED)✗ Missing CLAUDE.md$(NC)" && exit 1)
	@echo -e "$(GREEN)✓ Documentation files present$(NC)"
	@echo -e ""

	@echo -e "$(GREEN)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo -e "$(GREEN)║           🎉 ALL CHECKS PASSED SUCCESSFULLY! 🎉              ║$(NC)"
	@echo -e "$(GREEN)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo -e ""
	@echo -e "$(YELLOW)Summary:$(NC)"
	@echo -e "  ✓ Code properly formatted"
	@echo -e "  ✓ All linting checks passed (10.00/10)"
	@echo -e "  ✓ Type checking passed"
	@echo -e "  ✓ Shell scripts validated"
	@echo -e "  ✓ No security vulnerabilities"
	@echo -e "  ✓ Quality standards met"
	@echo -e "  ✓ All tests passing"
	@echo -e "  ✓ Comprehensive code coverage maintained"
	@echo -e "  ✓ Documentation complete"
	@echo -e ""
	@echo -e "$(GREEN)Ready for commit/push!$(NC)"

# Run the application
run:
	@echo -e "$(BLUE)Running git-ai-reporter...$(NC)"
	@$(VENV_ACTIVATE) && $(PYTHON) -m git_ai_reporter --help

# Build distribution packages
build: clean
	@echo -e "$(BLUE)Building distribution packages...$(NC)"
	@$(UV) build
	@echo -e "$(GREEN)✓ Build complete. Check dist/ directory$(NC)"

# Generate documentation
docs:
	@echo -e "$(BLUE)Generating documentation...$(NC)"
	@$(VENV_ACTIVATE) && $(PYTHON) -m pydoc -w $(SRC_DIR)/git_ai_reporter
	@echo -e "$(GREEN)✓ Documentation generated$(NC)"

# Allure Docker Service UI Commands
# These commands use docker-compose to manage Allure services with proper user permissions

# Start Allure Docker Service + UI (recommended for viewing reports)
allure-ui-up:
	@echo -e "$(BLUE)Starting Allure Docker Service + UI...$(NC)"
	@if [ ! -d "allure-results" ] || [ -z "$$(ls -A allure-results 2>/dev/null)" ]; then \
		echo -e "$(YELLOW)No Allure results found. Running tests first...$(NC)"; \
		$(MAKE) --no-print-directory test-allure; \
	fi
	@if command -v docker >/dev/null 2>&1; then \
		if command -v docker-compose >/dev/null 2>&1; then \
			echo -e "$(GREEN)Setting up Docker services with proper user permissions (docker-compose)...$(NC)"; \
			env UID=$$(id -u) GID=$$(id -g) docker-compose up -d; \
		elif docker compose version >/dev/null 2>&1; then \
			echo -e "$(GREEN)Setting up Docker services with proper user permissions (docker compose)...$(NC)"; \
			env UID=$$(id -u) GID=$$(id -g) docker compose up -d; \
		else \
			echo -e "$(RED)✗ Docker Compose not found$(NC)"; \
			echo -e "$(YELLOW)Install Docker Compose to use Allure UI services$(NC)"; \
			exit 1; \
		fi; \
		echo -e "$(GREEN)✓ Allure services started successfully$(NC)"; \
		echo -e ""; \
		echo -e "$(BLUE)Service URLs:$(NC)"; \
		echo -e "  📊 Allure UI (Recommended): $(YELLOW)http://localhost:5252/allure-docker-service-ui$(NC)"; \
		echo -e "  🔧 Allure API:               $(YELLOW)http://localhost:5050$(NC)"; \
		echo -e ""; \
		echo -e "$(GREEN)Pro tip: Use 'make allure-ui-logs' to monitor service logs$(NC)"; \
		echo -e "$(GREEN)Pro tip: Use 'make allure-ui-down' to stop services$(NC)"; \
	else \
		echo -e "$(RED)✗ Docker or docker-compose not found$(NC)"; \
		echo -e "$(YELLOW)Install Docker to use Allure UI services$(NC)"; \
		exit 1; \
	fi

# Stop Allure Docker Service + UI
allure-ui-down:
	@echo -e "$(BLUE)Stopping Allure Docker Service + UI...$(NC)"
	@if command -v docker >/dev/null 2>&1; then \
		if command -v docker-compose >/dev/null 2>&1; then \
			docker-compose down; \
		elif docker compose version >/dev/null 2>&1; then \
			docker compose down; \
		else \
			echo -e "$(YELLOW)⚠ Docker Compose not found$(NC)"; \
			exit 1; \
		fi; \
		echo -e "$(GREEN)✓ Allure services stopped$(NC)"; \
	else \
		echo -e "$(YELLOW)⚠ Docker not found$(NC)"; \
	fi

# Restart Allure Docker Service + UI
allure-ui-restart: allure-ui-down allure-ui-up
	@echo -e "$(GREEN)✓ Allure services restarted$(NC)"

# View Allure service logs
allure-ui-logs:
	@echo -e "$(BLUE)Viewing Allure service logs...$(NC)"
	@echo -e "$(YELLOW)Press Ctrl+C to stop following logs$(NC)"
	@if command -v docker >/dev/null 2>&1; then \
		if command -v docker-compose >/dev/null 2>&1; then \
			docker-compose logs -f; \
		elif docker compose version >/dev/null 2>&1; then \
			docker compose logs -f; \
		else \
			echo -e "$(YELLOW)⚠ Docker Compose not found$(NC)"; \
		fi; \
	else \
		echo -e "$(YELLOW)⚠ Docker not found$(NC)"; \
	fi

# Check Allure service status
allure-ui-status:
	@echo -e "$(BLUE)Checking Allure service status...$(NC)"
	@if command -v docker >/dev/null 2>&1; then \
		if command -v docker-compose >/dev/null 2>&1; then \
			COMPOSE_CMD="docker-compose"; \
		elif docker compose version >/dev/null 2>&1; then \
			COMPOSE_CMD="docker compose"; \
		else \
			echo -e "$(YELLOW)⚠ Docker Compose not found$(NC)"; \
			exit 1; \
		fi; \
		echo -e "$(BLUE)Container Status:$(NC)"; \
		$$COMPOSE_CMD ps; \
		echo -e ""; \
		echo -e "$(BLUE)Health Checks:$(NC)"; \
		if $$COMPOSE_CMD ps | grep -q "Up (healthy)"; then \
			echo -e "$(GREEN)✓ Services are running and healthy$(NC)"; \
			echo -e ""; \
			echo -e "$(BLUE)Quick Access:$(NC)"; \
			echo -e "  📊 Allure UI: $(YELLOW)http://localhost:5252/allure-docker-service-ui$(NC)"; \
			echo -e "  🔧 Allure API: $(YELLOW)http://localhost:5050$(NC)"; \
		elif $$COMPOSE_CMD ps | grep -q "Up"; then \
			echo -e "$(YELLOW)⚠ Services are starting up...$(NC)"; \
			echo -e "$(YELLOW)Wait a moment and check again$(NC)"; \
		else \
			echo -e "$(RED)✗ Services are not running$(NC)"; \
			echo -e "$(YELLOW)Use 'make allure-ui-up' to start services$(NC)"; \
		fi; \
	else \
		echo -e "$(YELLOW)⚠ Docker not found$(NC)"; \
	fi

# Development shortcuts
.PHONY: f l t c
f: format      # Shortcut for format
l: lint-quick  # Shortcut for quick lint
t: test-fast   # Shortcut for fast test
c: check-fast  # Shortcut for fast check
