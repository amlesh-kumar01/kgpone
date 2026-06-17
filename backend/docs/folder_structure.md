# Folder Structure

The repository follows a clean, decoupled Domain-Driven Design (DDD) approach.

```text
backend/
├── alembic/                # Database migrations for PostgreSQL
├── docs/                   # Developer documentation
├── src/                    # Main application source code
│   ├── api/                # API Presentation Layer
│   │   ├── middleware/     # Auth, Logging, Security Middlewares
│   │   ├── routes/         # FastAPI Routers (e.g. user_routes, course_routes)
│   │
│   ├── config/             # Application configuration mapping from .env
│   │
│   ├── infrastructure/     # External connections (Database, Qdrant, Celery setup)
│   │
│   ├── models/             # SQLAlchemy ORM Models (Database Tables)
│   │
│   ├── repositories/       # Data Access Layer (Postgres CRUD, Qdrant, S3)
│   │
│   ├── schemas/            # Pydantic validation schemas (Input/Output format)
│   │
│   ├── services/           # Core Business Logic Layer
│   │   ├── auth/           # JWT generation, role validation
│   │   ├── ingestion/      # The Ingestion Pipeline (Upload, Parsing, Chunking)
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
