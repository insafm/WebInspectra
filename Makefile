# Makefile for WebInspectra

# Variables
PYTHON := python3
PIP := pip
VENV := venv
PACKAGE_NAME := WebInspectra
TEST_DIR := WebInspectra/tests
README := README.md

# Default target
.PHONY: all
all: install

# Create virtual environment
.PHONY: venv
venv:
	@$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created in '$(VENV)'"

# Install dependencies
.PHONY: install
install: venv
	@. $(VENV)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	@. $(VENV)/bin/activate && $(PIP) install -r requirements.txt
	@. $(VENV)/bin/activate && $(PIP) install -e .
	@echo "Dependencies installed"

# Run tests
.PHONY: test
test:
	@. $(VENV)/bin/activate && pytest $(TEST_DIR)

# Clean build artifacts
.PHONY: clean
clean:
	@rm -rf build dist *.egg-info
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@echo "Cleaned build artifacts"

# Build the package
.PHONY: build
build: clean
	@. $(VENV)/bin/activate && $(PYTHON) setup.py sdist bdist_wheel
	@echo "Package built"

# Show help
.PHONY: help
help:
	@echo "Usage: make [TARGET]"
	@echo ""
	@echo "Targets:"
	@echo "  venv          Create virtual environment"
	@echo "  install       Install dependencies"
	@echo "  install-dev   Install development dependencies"
	@echo "  test          Run tests"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build the package"
	@echo "  help          Show this help message"
