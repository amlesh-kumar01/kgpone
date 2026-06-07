# KgpOne

KnowledgeOS Monorepo - A Deep Learning Agent architecture powered by React, FastAPI, LangGraph, and LocalStack.

## Setup Instructions

### 1. Prerequisites
- Docker & Docker Compose
- Node.js (for frontend)
- `uv` (for Python dependency management)

### 2. Infrastructure
Run the local infrastructure via Docker Compose:
```bash
docker-compose up -d
```
This will start PostgreSQL, Qdrant, Neo4j, and LocalStack (S3).

### 3. Backend Setup
1. Change to the backend directory: `cd backend`
2. Sync dependencies: `uv sync`
3. Run FastAPI server: `uv run uvicorn src.main:app --reload`

### 4. Frontend Setup
1. Change to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Start the dev server: `npm run dev`
