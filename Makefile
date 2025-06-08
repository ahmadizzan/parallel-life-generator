.PHONY: all install lint format test clean

PYTHON = ./.venv/bin/python
RUFF = ./.venv/bin/ruff
BLACK = ./.venv/bin/black
PYTEST = ./.venv/bin/pytest

# Default command: run all checks
all: lint test

# Install dependencies
install:
	poetry install

# Lint and format check
lint:
	$(RUFF) check .
	$(BLACK) --check .

# Auto-format code
format:
	$(BLACK) .

# Run tests
test:
	$(PYTEST)

# Clean up caches and virtual environments
clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache
	poetry env remove --all 