# KnowledgeOS Backend Rules and Conventions

This file defines the strict architectural rules, folder structures, and coding conventions for the `KgpOne/backend` project. 
**ALL AI AGENTS AND DEVELOPERS MUST ADHERE STRICTLY TO THESE RULES.**

## 1. Core Architecture Principles
The backend uses a strict **4-layer Domain-Driven Design (DDD)** architecture with unidirectional dependencies:
1. **Routes (Presentation Layer)**: Receives HTTP requests, validates via Pydantic, delegates to Services.
2. **Services (Business Logic Layer)**: Contains core business logic. NEVER accesses the database or external APIs directly. Calls Repositories.
3. **Repositories (Data Access Layer)**: Handles raw database queries (PostgreSQL, Qdrant, Neo4j) and returns ORM models.
4. **Infrastructure**: Connection factories (FastAPI app setup, SQLAlchemy engine, Celery broker, Qdrant client, Neo4j driver).

**Dependency Injection**: Use FastAPI `Depends()` to inject Services into Routes. Repositories are injected into Services via Factory functions (e.g., `get_user_service()`).

## 2. Directory Structure

```text
backend/
├── alembic/                # Database migrations (PostgreSQL)
├── docs/                   # System documentation (API, GraphRAG, Architecture)
├── src/                    # Source code root
│   ├── api/                # HTTP Routes, Middleware, Exceptions
│   ├── config/             # Environment variables (Pydantic Settings)
│   ├── infrastructure/     # DB Connectors (Neo4j, Postgres, Qdrant, Redis, S3)
│   ├── mcp/                # Model Context Protocol (FastMCP) Server & Tools
│   ├── models/             # SQLAlchemy ORM Models
│   ├── repositories/       # Data Access Layer (CRUD, Cypher, Vector Search)
│   ├── schemas/            # Pydantic Input/Output Schemas
│   ├── services/           # Business Logic Layer (Auth, Academic, RAG, Ingestion)
│   ├── utils/              # Abstract Interfaces (`interfaces.py`), Logging
│   └── workers/            # Celery Async Background Tasks
```

## 3. Strict Placement Rules
You must never place logic outside of its designated layer.
- **Routes (`src/api/routes/`)**: `{domain}_routes.py`
- **Models (`src/models/`)**: `{domain}_model.py` (SQLAlchemy only)
- **Schemas (`src/schemas/`)**: `{domain}_schema.py` (Pydantic only)
- **Repositories (`src/repositories/{engine}/`)**: `{domain}_repository.py`
- **Services (`src/services/{domain}/`)**: `{domain}_service.py`
- **Interfaces (`src/utils/interfaces.py`)**: All database repos must implement abstract interfaces (e.g. `IVectorRepo`, `IGraphRepository`).

## 4. SOLID Principles
- **Single Responsibility**: Each file handles exactly one domain (e.g., `user_routes.py`, `UserService`, `UserRepository`).
- **Open/Closed**: Use abstract base classes (e.g., `BaseQueryPlanner`, `BaseRetriever`) to extend functionality without modifying existing code.
- **Dependency Inversion**: Routes depend on service abstractions. Services depend on repository abstractions. No layer should depend on a concrete implementation from a lower layer.

## 5. Naming Conventions
- **Classes**: `PascalCase` (e.g., `UserService`, `DocumentRepository`, `UserCreate`)
- **Functions/Methods**: `snake_case` (e.g., `authenticate_user`, `get_by_id`)
- **Interfaces**: Prefixed with `I` (e.g., `IVectorRepo`)

## 6. Standardized API Response
ALL HTTP endpoint responses must return the `StandardResponse` model located in `src/schemas/response_schema.py`.
```json
{
    "status": "success",
    "message": "Human-readable description",
    "data": { ... }
}
```

## 7. RAG & Graph Pipeline Rules
- **Extraction**: Entities and relationships are extracted via LLM during the ingestion Celery task.
- **Neo4j Cypher**: Do NOT run raw Cypher strings inside services. All Cypher queries must be encapsulated inside `GraphRepository`.
- **Query Planner**: All hybrid RAG queries must pass through `NLPPlannerService` (TF-IDF + SVM intent classifier).
- **Reranking**: Use `CrossEncoderRerankService` (HuggingFace Inference API) for chunk reranking.
- **Retrieval**: Use `asyncio.gather()` for parallel backend retrieval and Reciprocal Rank Fusion (RRF) for merging results.
- **Semantic Cache**: All `/query/ask` requests check `SemanticCacheService` (Redis) before running the pipeline. Cache scope is per-`course_offering_id` if present, otherwise global.

Do not deviate from these established patterns when modifying the backend.
