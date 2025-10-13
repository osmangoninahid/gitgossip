.PHONY: help install lint format typecheck test run build clean

PYTHON := uv run
PACKAGE := gitgossip

help:
	@echo ""
	@echo "GitGossip Developer Commands"
	@echo "--------------------------------"
	@echo "make install        - Install dependencies using uv"
	@echo "make lint           - Run Ruff linter"
	@echo "make format         - Auto-format code with Black and Ruff"
	@echo "make test           - Run pytest suite"
	@echo "make run CMD='...'  - Run gitgossip CLI command"
	@echo "make clean          - Remove build/test artifacts"
	@echo ""

install:
	@echo "🔧 Installing dependencies..."
	uv sync --all-extras
	@echo "✅ Dependencies installed."

lint:
	@echo "🔍 Running Ruff..."
	$(PYTHON) ruff check

format:
	@echo "🎨 Formatting with Black and Ruff..."
	$(PYTHON) black .
	$(PYTHON) ruff check --fix

test:
	@echo "🧪 Running tests with pytest..."
	$(PYTHON) pytest -v --disable-warnings

run:
	@echo "🚀 Running GitGossip..."
	$(PYTHON) gitgossip $(CMD)

clean:
	@echo "🧹 Cleaning up build artifacts..."
	rm -rf .pytest_cache .mypy_cache dist build *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✅ Cleanup complete."
