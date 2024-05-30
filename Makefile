# Makefile for WebInspectra

# Variables
PYTHON := python3
PIP := pip
VENV := venv
PACKAGE_NAME := WebInspectra
TEST_DIR := tests
README := README.md

# Default target
.PHONY: all
all: install

# Ensure virtualenv is installed
.PHONY: ensure-virtualenvmake venv
ensure-virtualenv:
	@$(PIP) install --user virtualenv
	@echo "Virtualenv installed"

# Create virtual environment
.PHONY: venv
venv: ensure-virtualenv
	@$(PYTHON) -m virtualenv $(VENV)
	@echo "Virtual environment created in '$(VENV)'"

# Install dependencies
.PHONY: install
install: venv
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	@. $(VENV)/bin/activate && $(PIP) install -e .
	@echo "Dependencies installed"

# Run tests
.PHONY: test
test: check-venv
	@. $(VENV)/bin/activate && pytest $(TEST_DIR)
	@echo "Tests completed"

# Check if virtual environment exists or create it
.PHONY: check-venv
check-venv:
	@if [ ! -d "$(VENV)/bin" ]; then \
		echo "Virtual environment not found. Creating '$(VENV)'..."; \
		$(MAKE) venv; \
		$(MAKE) install; \
	fi

# Clean build artifacts and virtual environment
.PHONY: clean
clean:
	@if [ -d "$(VENV)" ]; then . $(VENV)/bin/activate && deactivate; fi
	@rm -rf $(VENV)
	@rm -rf build dist *.egg-info .pytest_cache
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@echo "Cleaned build artifacts and virtual environment"

# Build the package
.PHONY: build
build: clean check-venv
	@. $(VENV)/bin/activate && $(PYTHON) setup.py sdist bdist_wheel
	@. $(VENV)/bin/activate && $(PIP) install twine
	@. $(VENV)/bin/activate && twine upload dist/*
	@echo "Package built and uploaded"

# Show help
.PHONY: help
help:
	@echo "Usage: make [TARGET]"
	@echo ""
	@echo "Targets:"
	@echo "  ensure-virtualenv  Ensure virtualenv is installed"
	@echo "  venv               Create virtual environment"
	@echo "  install            Install dependencies"
	@echo "  test               Run tests"
	@echo "  clean              Clean build artifacts and virtual environment"
	@echo "  build              Build the package"
	@echo "  help               Show this help message"
