# KgpOne (Academic Nexus)

KnowledgeOS Monorepo — A secure Deep Learning Agent and GraphRAG curriculum reasoning engine powered by React, FastAPI, LangGraph, Qdrant, Neo4j, and LocalStack.

---

## 🚀 Key Architectural Features

### 1. GraphRAG Retrieval Pipeline & Cosine Matching
Combines semantic vector search with hierarchical Knowledge Graph context. User queries are embedded (using Gemini `text-embedding-004` or a deterministic local Feature Hashing fallback) and matched against slide/text chunks in **Qdrant** utilizing cosine similarity metrics.

### 2. Curriculum Time Travel (Autonomous Prerequisite Bridge)
When a student asks about an advanced topic (e.g. A* heuristics or pathfinding algorithms), the engine queries the **Neo4j Graph Database**, walking backwards down `[HAS_PREREQUISITE]` concept dependency chains. It diagnoses missing background knowledge and retrieves foundational explanation slides from prior semesters (e.g. 2nd Year Discrete Mathematics) to ground the answer.

### 3. Knowledge Provenance (AI Explainability)
Every answer is accompanied by verifiable citation metadata showing exactly where the supporting evidence was sourced. Each chunk is tracked by document title, course code, section header, page/slide number, and confidence levels.

### 4. Dual-Mode Resilience (Offline-First Fallback)
If local Docker services (Qdrant, Neo4j) or external APIs (Gemini) are unavailable, the backend automatically activates localized, in-memory Python fallbacks (Feature Hashing vectorizer, local graph walk, and rule-based template synthesizer) to remain 100% functional.

### 5. Secure Upload & Ingestion
- **Direct-to-S3 Uploads**: Utilizes presigned PUT URLs via LocalStack S3 to securely stream documents directly from the frontend, bypassing memory limits.
- **LlamaParse Integration**: Parses complex lecture notes PDFs asynchronously (using FastAPI background tasks or Celery/Redis workers) to extract clean, math-enabled LaTeX markdown.

---

## 📁 Repository Structure

```
kgpone/
├── backend/
│   ├── src/
│   │   ├── config/          # DB & Client configurations (Qdrant, Neo4j, Postgres)
│   │   ├── routes/          # REST Endpoints (Auth, Chat/Query, Uploads, Tasks)
│   │   ├── services/
│   │   │   ├── ingestion/   # Document chunking and embedding services
│   │   │   ├── graph/       # Neo4j query and prerequisite traversal services
│   │   │   └── rag/         # Hybrid retrieval, reranking, and citation generation
│   │   └── tests/           # Automated test suites
│   ├── Dockerfile
│   └── pyproject.toml       # Python dependencies managed by 'uv'
├── frontend/
│   ├── src/                 # React SPA (Tailwind + CSS Design Tokens)
│   ├── tailwind.config.js
│   └── package.json
└── docker-compose.yml       # Local infrastructure setup
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- Docker & Docker Compose
- Node.js (v18+) & npm
- `uv` (Fast Python package installer)

### 2. Run Local Infrastructure
Start Qdrant, Neo4j, Redis, PostgreSQL, and LocalStack (S3) containers:
```bash
docker-compose up -d
```

### 3. Configure Environment Variables
Create a `.env` file inside the `backend` directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/kgpone
QDRANT_URL=http://localhost:6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
S3_ENDPOINT_URL=http://localhost:4566
S3_BUCKET_NAME=kgpone-assets
GEMINI_API_KEY=your_gemini_api_key_here
LLAMA_CLOUD_API_KEY=your_llamaparse_key_here
```

### 4. Run Backend Server
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Sync python virtual environment and dependencies:
   ```bash
   uv sync
   ```
3. Run the development API server:
   ```bash
   uv run uvicorn src.app:app --reload
   ```
   *Interactive API Swagger docs are hosted at [http://localhost:8000/docs](http://localhost:8000/docs).*

### 5. Run Frontend Server
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Launch the Vite dev server:
   ```bash
   npm run dev
   ```
   *Open [http://localhost:5173/](http://localhost:5173/) to launch the visual interface.*

---

## 🧪 Verification & Testing

Verify that all ingestion, graph reasoning, and vector search features are functioning correctly:
```bash
cd backend
uv run python -m unittest src.tests.test_rag_pipeline
```
