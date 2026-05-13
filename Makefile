REPO_ROOT := $(CURDIR)
FRONTEND_DIR := $(REPO_ROOT)/frontend

PYTHON ?= python3
NPM ?= npm

.PHONY: help install install-backend install-frontend init-db dev-backend dev-frontend \
	backend-compile backend-smoke backend-validate frontend-lint frontend-build \
	lint build validate package-backend clean

help:
	@printf '%s\n' \
		'install           Install backend and frontend dependencies' \
		'install-backend   Install Python dependencies from requirements.txt' \
		'install-frontend  Install frontend dependencies with npm ci' \
		'init-db           Create database tables using scripts/init_db.py' \
		'dev-backend       Run the FastAPI app with uvicorn reload enabled' \
		'dev-frontend      Run the Vite development server' \
		'backend-validate  Compile Python sources and smoke test /health' \
		'frontend-lint     Run the frontend ESLint checks' \
		'frontend-build    Build the frontend production bundle' \
		'lint              Run all lint steps exposed by the repository' \
		'build             Produce backend and frontend build artifacts' \
		'validate          Run backend validation plus frontend lint/build' \
		'package-backend   Create dist/facttrack-backend-src.tar.gz' \
		'clean             Remove generated build artifacts'

install: install-backend install-frontend

install-backend:
	cd $(REPO_ROOT) && $(PYTHON) -m pip install -r requirements.txt

install-frontend:
	cd $(FRONTEND_DIR) && $(NPM) ci

init-db:
	cd $(REPO_ROOT) && $(PYTHON) -m scripts.init_db

dev-backend:
	cd $(REPO_ROOT) && $(PYTHON) -m uvicorn app.main:app --reload

dev-frontend:
	cd $(FRONTEND_DIR) && $(NPM) run dev

backend-compile:
	cd $(REPO_ROOT) && $(PYTHON) -m compileall app ingestion scripts

backend-smoke:
	cd $(REPO_ROOT) && $(PYTHON) -c "from fastapi.testclient import TestClient; from app.main import app; response = TestClient(app).get('/health'); assert response.status_code == 200, response.text; print('backend health smoke test passed')"

backend-validate: backend-compile backend-smoke

frontend-lint:
	cd $(FRONTEND_DIR) && $(NPM) run lint

frontend-build:
	cd $(FRONTEND_DIR) && $(NPM) run build

lint: frontend-lint

build: package-backend frontend-build

validate: backend-validate frontend-lint frontend-build

package-backend:
	cd $(REPO_ROOT) && mkdir -p dist && tar --exclude='__pycache__' --exclude='*.pyc' --exclude='.pytest_cache' -czf dist/facttrack-backend-src.tar.gz app ingestion scripts requirements.txt README.md .env.example

clean:
	cd $(REPO_ROOT) && rm -rf dist
	cd $(FRONTEND_DIR) && rm -rf dist
