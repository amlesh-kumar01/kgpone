# KgpOne Backend API

Welcome to the KgpOne Backend! This repository serves as the intelligence and API layer for the platform, leveraging modern FastAPI, Celery, Docling, Gemini, PostgreSQL, and Qdrant to ingest and retrieve academic documents securely.

## 📚 Developer Documentation
To understand how the system is architected, please read the documentation inside the `/docs` folder:

1. [Project Information](docs/project_info.md)
2. [Folder Structure (DDD)](docs/folder_structure.md)
3. [API Guidelines & RBAC](docs/api_guidelines.md)
4. [Schema & Database Explanation](docs/schema_explanation.md)
5. [The Modular AI Ingestion Pipeline](docs/ingestion.md)

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (Extremely fast Python package manager)
- Docker & Docker Compose

### 1. Environment Setup
Copy the example environment file and configure your API keys (especially `GEMINI_API_KEY`, and `HUGGINGFACE_API_KEY` for the cross-encoder).
```bash
cp .env.example .env
```

### 2. Install Dependencies
Use `uv` to automatically sync the lockfile into a virtual environment.
```bash
uv sync
```

### 3. Start Infrastructure Dependencies
The backend relies on external cloud providers for PostgreSQL and Qdrant. However, for local asynchronous queue management, we must run Redis.
```bash
# Go to the parent directory and spin up Redis
cd ../
docker compose up -d redis
```

### 4. Run Database Migrations
Ensure your remote/local PostgreSQL database is fully migrated to the latest schema:
```bash
cd backend/
uv run alembic upgrade head
```

### 5. Train NLP Intent Classifier
Before starting the server, train the lightweight intent classifier model (this generates the `.pkl` files locally):
```bash
uv run python -m src.scripts.train_intent_classifier
```

### 6. Start the FastAPI Server
Spin up the main application. It will run on `http://localhost:8000`.
```bash
uv run uvicorn src.main:app --reload
```
You can now access the interactive Swagger documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### 7. Start the Celery Worker
To enable the background AI ingestion pipeline (which parses PDFs and embeds chunks into Qdrant), you must run the Celery worker in a separate terminal:
```bash
uv run celery -A src.workers.app.celery_app worker --loglevel=info
```
> [!NOTE]
> **Windows Users**: Celery does not fully support Windows natively. If you encounter a `PermissionError: [WinError 5] Access is denied` or `billiard` process crashes, append `--pool=solo` to the command:
> ```bash
> uv run celery -A src.workers.app.celery_app worker --loglevel=info --pool=solo
> ```
---
Happy Coding!
