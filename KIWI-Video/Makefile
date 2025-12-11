.PHONY: setup install dev test lint format clean

# Setup development environment
setup:
	@echo "Setting up KIWI-Video development environment..."
	python -m pip install --upgrade pip
	pip install -e ".[dev]"

# Install dependencies only
install:
	pip install -e .

# Run development server
dev:
	uvicorn kiwi_video.api.app:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest tests/ -v --cov=kiwi_video --cov-report=html

# Run linting
lint:
	@echo "Running ruff..."
	ruff check kiwi_video/
	@echo "Running mypy..."
	mypy kiwi_video/

# Format code
format:
	@echo "Formatting with ruff..."
	ruff format kiwi_video/
	ruff check --fix kiwi_video/

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov/ .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run full check (lint + test)
check: lint test

# Build Docker image
docker-build:
	docker-compose build

# Run with Docker
docker-up:
	docker-compose up -d

# Stop Docker containers
docker-down:
	docker-compose down

# View logs
docker-logs:
	docker-compose logs -f

# Help
help:
	@echo "Available commands:"
	@echo "  make setup         - Setup development environment"
	@echo "  make install       - Install dependencies"
	@echo "  make dev           - Run development server"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo "  make check         - Run lint and test"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"

