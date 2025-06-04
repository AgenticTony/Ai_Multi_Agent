.PHONY: help install test lint format check-style run-dev run-docker build-docker clean

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install dependencies using Poetry"
	@echo "  test         Run tests with pytest"
	@echo "  test-cov     Run tests with coverage report"
	@echo "  lint         Run linting (flake8, mypy)"
	@echo "  format       Format code (black, isort)"
	@echo "  check-style  Check code style without making changes"
	@echo "  run-dev      Run development server"
	@echo "  run-docker   Build and run Docker container"
	@echo "  build-docker Build Docker image"
	@echo "  clean        Clean up temporary files"
	@echo "  pre-commit   Install and run pre-commit hooks"

# Development setup
install:
	poetry install --with dev,test

install-prod:
	poetry install --only main

# Testing
test:
	poetry run pytest -v tests/

test-cov:
	poetry run pytest --cov=app --cov-report=html --cov-report=term-missing tests/

test-watch:
	poetry run pytest-watch -- tests/

# Code quality
lint:
	poetry run flake8 app tests
	poetry run mypy app

format:
	poetry run black app tests
	poetry run isort app tests

check-style:
	poetry run black --check app tests
	poetry run isort --check-only app tests
	poetry run flake8 app tests

# Security
security:
	poetry run bandit -r app/
	poetry run safety check

# Development server
run-dev:
	poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Docker operations
build-docker:
	docker build -t voicehive-backend .

run-docker: build-docker
	docker run -p 8000:8000 --env-file .env voicehive-backend

run-docker-dev: build-docker
	docker run -p 8000:8000 --env-file .env -v $(PWD):/app voicehive-backend

# Pre-commit hooks
pre-commit-install:
	poetry run pre-commit install

pre-commit:
	poetry run pre-commit run --all-files

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

# Database operations (for future use)
db-upgrade:
	@echo "Database migrations not implemented yet"

db-downgrade:
	@echo "Database migrations not implemented yet"

# Documentation
docs:
	@echo "Documentation generation not implemented yet"

# CI/CD helpers
ci-test: install test lint security

ci-build: clean build-docker

# Environment setup
setup-dev: install pre-commit-install
	@echo "Development environment setup complete!"
	@echo "Run 'make run-dev' to start the development server"
