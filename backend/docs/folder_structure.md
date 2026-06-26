# Folder Structure

The repository follows a clean, decoupled Domain-Driven Design (DDD) approach.

```text
backend/
├── alembic/                # Database migrations for PostgreSQL
├── docs/                   # Developer documentation
├── src/                    # Main application source code
│   ├── api/                # API Presentation Layer
│   │   ├── middleware/     # Auth, Logging, Security Middlewares
│   │   ├── routes/         # FastAPI Routers (e.g. user_routes, academic_routes)
│   │
│   ├── mcp/                # Standalone FastMCP Server components
│   │   ├── server.py       # MCP Server instance
│   │   ├── tools.py        # External tools exposed to AI Assistants
│   │   └── prompts.py      # Predefined AI prompts (Study guide, etc.)
│   │
│   ├── config/             # Application configuration mapping from .env
│   │
│   ├── infrastructure/     # External connections (Database, Qdrant, Celery, Neo4j)
│   │
│   ├── models/             # SQLAlchemy ORM Models (Database Tables)
│   │
│   ├── repositories/       # Data Access Layer (Postgres, Qdrant, S3, Neo4j Graph)
│   │
│   ├── schemas/            # Pydantic validation schemas (Input/Output format)
│   │
│   ├── services/           # Core Business Logic Layer
│   │   ├── auth/           # JWT generation, role validation
│   │   ├── ingestion/      # The Ingestion Pipeline (Upload, Parsing, Chunking, Extraction)
│   │   ├── graph/          # Graph construction and relationship management
│   │   └── rag/            # Hybrid Retrieval-Augmented Generation logic (Planner, Reranker, Retrieval)
│   │
│   ├── utils/              # Helpers and abstract Interfaces (`interfaces.py`)
│   │
│   └── workers/            # Background Tasks (Celery workers & pipelines)
│       ├── app.py          # Celery instance initializer
│       └── tasks/          # Executable @shared_task functions
│
├── .env.example            # Environment variables template
├── docker-compose.yml      # Root composition for Redis/Celery background dependencies
├── pyproject.toml          # Project dependencies (`uv` lock configuration)
└── README.md               # Quickstart guide
```

## Key Principles
- **No Circular Imports**: `api` imports from `services`, `services` import from `repositories` and `models`. Repositories never import from `services`.
- **Interface Segregation**: The vector DB is accessed through `IVectorRepo` found in `utils/interfaces.py`, allowing easy mocking for tests.
