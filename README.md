# KgpOne

KgpOne is an advanced AI-powered platform for academic knowledge management. It provides a robust backend for ingesting course documents, building semantic graphs, and generating insights, paired with a React frontend that includes an AI Analysis Admin Panel and a student-facing Course Exam Prep Studio.

## Architecture Highlights
- **Backend**: FastAPI, Celery, Docling (for advanced document parsing), Gemini, PostgreSQL, Qdrant, Neo4j.
- **Frontend**: React, Tailwind CSS, shadcn/ui, Vite.
- **AI Features**: Summarization, Quiz Generation, Formula Extraction, Concept Graphing, Document Comparison.

## Quick Start (Local Development)

We provide a convenient script to start all services locally on Windows.

1. Ensure Docker is running (for Redis).
2. Start Redis (used by Celery):
   ```bash
   docker compose up -d redis
   ```
3. Ensure `.env` is configured in the `backend/` directory.
4. Run the startup script from the root:
   ```bash
   start_local.bat
   ```
   This script will:
   - Run Alembic migrations
   - Start the FastAPI backend
   - Start the Celery worker
   - Start the Vite frontend dev server

## Documentation
- [Backend Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
