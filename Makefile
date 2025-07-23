.PHONY: setup test lint format clean run docker-build docker-run security-check help

# Variables
VENV = .venv
PYTHON = $(VENV)/Scripts/python
PIP = $(VENV)/Scripts/pip
PYTEST = $(VENV)/Scripts/pytest
FLASK = $(VENV)/Scripts/flask
PORT = 5000

help:
	@echo "Available commands:"
	@echo "  make setup         - Create virtual environment and install dependencies"
	@echo "  make lint          - Run linting checks"
	@echo "  make format        - Format code with black"
	@echo "  make clean         - Remove build artifacts and cache files"
	@echo "  make run           - Run the Flask application locally"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run application in Docker container"
	@echo "  make security-check - Run security checks"

setup:
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install black flake8 bandit safety


lint:
	$(VENV)/Scripts/flake8 app.py college_agent/

format:
	$(VENV)/Scripts/black app.py college_agent/

clean:
	rm -rf __pycache__
	rm -rf college_agent/__pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

run:
	$(PYTHON) app.py

docker-build:
	docker build -t college-agent .

docker-run:
	docker run -p $(PORT):5000 --env-file college_agent/.env college-agent

security-check:
	$(VENV)/Scripts/bandit -r app.py college_agent/
	$(VENV)/Scripts/safety check

# For Linux/Mac users, uncomment these lines and comment out the Windows versions above
# PYTHON = $(VENV)/bin/python
# PIP = $(VENV)/bin/pip
# PYTEST = $(VENV)/bin/pytest
# FLASK = $(VENV)/bin/flask