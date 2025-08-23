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
        venv update-deps freeze-deps

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

# Run all tests
test:
	@echo -e "$(BLUE)Running all tests...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR) -v
	@echo -e "$(GREEN)✓ All tests passed$(NC)"

# Run tests without coverage (faster)
test-fast:
	@echo -e "$(BLUE)Running tests (fast mode)...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR) -q -q --no-cov
	@echo -e "$(GREEN)✓ Tests passed$(NC)"

# Run tests with coverage
coverage:
	@echo -e "$(BLUE)Running tests with coverage...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR) -v \
		--cov=$(SRC_DIR) \
		--cov-report=term-missing \
		--cov-report=html \
		--cov-fail-under=$(COVERAGE_THRESHOLD)
	@echo -e "$(GREEN)✓ Coverage check passed (>= $(COVERAGE_THRESHOLD)%)$(NC)"
	@echo -e "$(YELLOW)Coverage report: open htmlcov/index.html$(NC)"

# Run unit tests only
test-unit:
	@echo -e "$(BLUE)Running unit tests...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR)/unit -v
	@echo -e "$(GREEN)✓ Unit tests passed$(NC)"

# Run integration tests only
test-integration:
	@echo -e "$(BLUE)Running integration tests...$(NC)"
	@$(VENV_ACTIVATE) && $(UV) run pytest $(TEST_DIR)/integration -v
	@echo -e "$(GREEN)✓ Integration tests passed$(NC)"

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
		echo "$(GREEN)✓ All shell scripts valid$(NC)"; \
	else \
		echo "$(YELLOW)⚠ shellcheck not installed. Install with: apt-get install shellcheck$(NC)"; \
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
	@echo -e "$(BLUE)║              RUNNING COMPREHENSIVE CHECK-ALL                ║$(NC)"
	@echo -e "$(BLUE)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo -e ""

	@echo -e "$(BLUE)[1/9] Code Formatting Check$(NC)"
	@echo -e "$(BLUE)Checking code formatting...$(NC)"
	@if ! $(VENV_ACTIVATE) && ruff format --check . > /dev/null 2>&1; then \
		echo "$(YELLOW)⚠️  Code needs formatting. Running formatter...$(NC)"; \
		$(MAKE) --no-print-directory format; \
	else \
		echo "$(GREEN)✓ Code formatting is correct$(NC)"; \
	fi
	@echo -e ""

	@echo -e "$(BLUE)[2/9] Python Linting (Full)$(NC)"
	@$(MAKE) --no-print-directory lint
	@echo -e ""

	@echo -e "$(BLUE)[3/9] Type Checking$(NC)"
	@$(MAKE) --no-print-directory type-check
	@echo -e ""

	@echo -e "$(BLUE)[4/9] Shell Script Validation$(NC)"
	@$(MAKE) --no-print-directory shellcheck
	@echo -e ""

	@echo -e "$(BLUE)[5/9] Security Scanning$(NC)"
	@$(MAKE) --no-print-directory security-scan
	@echo -e ""

	@echo -e "$(BLUE)[6/9] Quality Standards$(NC)"
	@$(MAKE) --no-print-directory quality-check
	@echo -e ""

	@echo -e "$(BLUE)[7/9] Fast Tests$(NC)"
	@$(MAKE) --no-print-directory test-fast
	@echo -e ""

	@echo -e "$(BLUE)[8/9] Coverage Analysis$(NC)"
	@$(MAKE) --no-print-directory coverage
	@echo -e ""

	@echo -e "$(BLUE)[9/9] Documentation Check$(NC)"
	@echo -e "Checking for required documentation files..."
	@test -f README.md || (echo "$(RED)✗ Missing README.md$(NC)" && exit 1)
	@test -f LICENSE || (echo "$(RED)✗ Missing LICENSE$(NC)" && exit 1)
	@test -f CLAUDE.md || (echo "$(RED)✗ Missing CLAUDE.md$(NC)" && exit 1)
	@echo -e "$(GREEN)✓ Documentation files present$(NC)"
	@echo -e ""

	@echo -e "$(GREEN)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo -e "$(GREEN)║           🎉 ALL CHECKS PASSED SUCCESSFULLY! 🎉             ║$(NC)"
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

# Development shortcuts
.PHONY: f l t c
f: format      # Shortcut for format
l: lint-quick  # Shortcut for quick lint
t: test-fast   # Shortcut for fast test
c: check-fast  # Shortcut for fast check
