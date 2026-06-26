# KgpOne Backend — API Documentation & Architecture Guide

> **Version**: 1.0  
> **Base URL**: `http://localhost:8000`  
> **API Prefix**: `/api/v1`

---

## Table of Contents

1. [Folder Structure & Rules](#1-folder-structure--rules)
2. [Architecture Principles](#2-architecture-principles)
3. [Naming Conventions](#3-naming-conventions)
4. [Dependency Injection Pattern](#4-dependency-injection-pattern)
5. [Standard API Response Format](#5-standard-api-response-format)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [API Endpoint Reference](#7-api-endpoint-reference)
   - [Root](#71-root)
   - [Users (Auth)](#72-users--authentication)
   - [Academic](#73-academic--departments)
   - [Documents](#74-documents)
8. [Data Models Reference](#8-data-models-reference)
9. [Error Handling](#9-error-handling)

---

## 1. Folder Structure & Rules

```
backend/
├── alembic/                    # Database migration scripts (Alembic)
│   └── env.py
├── docs/                       # Documentation files
│   ├── context.md              # System context & file directory map
│   └── api_docs.md             # This file — API reference & architecture guide
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── mcp.py                  # MCP (Model Context Protocol) stub
│   ├── mcp/                    # MCP server package
│   │   ├── server.py           # FastMCP server instance
│   │   ├── tools.py            # MCP tool registrations
│   │   └── prompts.py          # System prompts for LLM agents
│   ├── api/                    # ── PRESENTATION LAYER ──
│   │   ├── routes/             # HTTP endpoint definitions (controllers)
│   │   │   ├── user_routes.py
│   │   │   ├── academic_routes.py
│   │   │   ├── document_routes.py
│   │   │   └── query_routes.py # Hybrid RAG query endpoints
│   │   ├── middleware/         # Request/response interceptors
│   │   │   ├── auth_middleware.py
│   │   │   ├── cors_middleware.py
│   │   │   ├── request_logger.py
│   │   │   └── security_middleware.py
│   │   └── exceptions/        # Global error handlers
│   │       ├── handlers.py
│   │       └── openapi.py
│   ├── config/                 # ── CONFIGURATION LAYER ──
│   │   └── settings.py         # Pydantic Settings (reads .env)
│   ├── models/                 # ── DATA MODEL LAYER (SQLAlchemy ORM) ──
│   │   ├── user_model.py
│   │   ├── academic_model.py
│   │   ├── document_model.py
│   │   └── system_model.py
│   ├── schemas/                # ── VALIDATION LAYER (Pydantic Schemas) ──
│   │   ├── user_schema.py
│   │   ├── academic_schema.py
│   │   ├── document_schema.py
│   │   ├── query_schema.py     # Schemas for hybrid RAG search and ask
│   │   └── response_schema.py
│   ├── repositories/           # ── DATA ACCESS LAYER (Repository Pattern) ──
│   │   ├── postgres/
│   │   │   ├── user_repository.py
│   │   │   ├── academic_repository.py
│   │   │   └── document_repository.py
│   │   ├── qdrant/
│   │   │   └── vector_repository.py
│   │   ├── s3/
│   │   │   └── storage_repository.py
│   │   └── neo4j/
│   │       └── graph_repository.py # Graph logic via Cypher queries
│   ├── services/               # ── BUSINESS LOGIC LAYER ──
│   │   ├── auth/
│   │   │   └── user_service.py
│   │   ├── academic/
│   │   │   └── academic_service.py
│   │   ├── graph/
│   │   │   ├── graph_builder_service.py # Map entities to Neo4j
│   │   │   ├── graph_query_service.py
│   │   │   └── prerequisite_service.py
│   │   ├── rag/
│   │   │   ├── base.py                  # Base interfaces for RAG
│   │   │   ├── planner_service.py       # LLM query intent planner
│   │   │   ├── answer_service.py        # LLM final answer generator
│   │   │   ├── citation_service.py
│   │   │   ├── rerank_service.py        # LLM context reranking
│   │   │   └── retrieval_service.py     # Orchestrator for graph + vector search
│   │   └── ingestion/
│   │       ├── pipeline.py
│   │       ├── metadata_builder.py
│   │       ├── extraction/
│   │       │   ├── base.py
│   │       │   └── gemini_extractor.py  # LLM entity extraction
│   │       ├── chunking/
│   │       │   ├── base.py
│   │       │   └── recursive_chunker.py
│   │       ├── embedding/
│   │       │   ├── base.py
│   │       │   └── gemini_embedding.py
│   │       ├── parser/
│   │       │   ├── base.py
│   │       │   └── llama_parser.py
│   │       └── upload_manager/
│   │           └── document_service.py
│   ├── infrastructure/         # ── INFRASTRUCTURE CONNECTORS ──
│   │   ├── celery.py
│   │   ├── database.py
│   │   ├── neo4j.py
│   │   ├── qdrant.py
│   │   └── s3.py
│   ├── workers/                # ── ASYNC TASK LAYER (Celery) ──
│   │   ├── app.py
│   │   └── tasks/
│   │       ├── cleanup_tasks.py
│   │       └── ingestion_tasks.py
│   ├── utils/                  # ── SHARED UTILITIES ──
│   │   ├── interfaces.py       # Abstract base classes (contracts)
│   │   └── logger.py
│   └── scripts/                # ── DEV/OPS SCRIPTS ──
│       └── seed.py             # Database seeding script
├── alembic.ini
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

### Placement Rules

| File Type | Must Go In | Naming Convention |
|-----------|-----------|-------------------|
| HTTP route handlers | `src/api/routes/` | `{domain}_routes.py` |
| Middleware | `src/api/middleware/` | `{purpose}_middleware.py` |
| Exception handlers | `src/api/exceptions/` | Descriptive name |
| SQLAlchemy ORM models | `src/models/` | `{domain}_model.py` |
| Pydantic request/response schemas | `src/schemas/` | `{domain}_schema.py` |
| Repository classes (DB access) | `src/repositories/{engine}/` | `{domain}_repository.py` |
| Business logic services | `src/services/{domain}/` | `{domain}_service.py` |
| Infrastructure connectors | `src/infrastructure/` | `{engine_name}.py` |
| Celery background tasks | `src/workers/tasks/` | `{purpose}_tasks.py` |
| Abstract interfaces | `src/utils/interfaces.py` | Prefixed with `I` (e.g. `IVectorRepo`) |
| Configuration | `src/config/settings.py` | Single file, Pydantic Settings |

> **Rule**: Never place route logic, models, schemas, or services outside their designated directories. Each domain gets its own file within the appropriate layer directory.

---

## 2. Architecture Principles

### Layered Architecture

The codebase follows a strict **4-layer architecture** with unidirectional dependencies:

```
Routes (Presentation) → Services (Business Logic) → Repositories (Data Access) → Infrastructure (Connectors)
```

- **Routes** receive HTTP requests, validate input via Pydantic schemas, delegate to services, and return `StandardResponse`.
- **Services** contain all business rules. They never access the database directly — they call repositories.
- **Repositories** execute raw database queries and return ORM model instances. They have no business logic.
- **Infrastructure** provides connection factories (DB sessions, S3 clients, Qdrant clients).

### SOLID Principles

| Principle | How It's Applied |
|-----------|-----------------|
| **S — Single Responsibility** | Each file handles one domain. `user_routes.py` only handles user HTTP logic; `UserService` only handles user business logic; `UserRepository` only handles user DB queries. |
| **O — Open/Closed** | Ingestion pipeline components (chunkers, embedders, parsers) extend abstract base classes (`base.py`) without modifying existing implementations. Add a new parser by creating a new file, not editing `llama_parser.py`. |
| **L — Liskov Substitution** | All concrete repository implementations (`QdrantRepository`, `S3Storage`, `GraphRepository`) satisfy their abstract interface contracts in `utils/interfaces.py`. Any implementation can be swapped without breaking callers. |
| **I — Interface Segregation** | Separate interfaces for each infrastructure concern: `IVectorRepo`, `IS3Storage`, `IGraphRepository`, `IRetrievalService`. Consumers depend only on the interface they need. |
| **D — Dependency Inversion** | Routes depend on service abstractions injected via FastAPI's `Depends()`. Services depend on repository abstractions. No layer depends on a concrete implementation from a lower layer. |

### OOP Patterns

| Pattern | Usage |
|---------|-------|
| **Repository Pattern** | All data access is encapsulated in repository classes (`UserRepository`, `DocumentRepository`, `AcademicRepository`, `QdrantRepository`, `S3Storage`, `GraphRepository`). |
| **Service Layer** | Business rules are centralized in service classes (`UserService`, `AcademicService`, `DocumentService`). |
| **Factory Method** | `get_user_service()`, `get_document_service()`, `get_academic_service()` — route-level factories create service instances with injected dependencies. |
| **Strategy Pattern** | Ingestion pipeline uses interchangeable strategies for chunking, embedding, and parsing via abstract base classes. |
| **Abstract Base Classes** | `IVectorRepo`, `IS3Storage`, `IGraphRepository`, `IRetrievalService` in `utils/interfaces.py` define contracts for infrastructure components. |

---

## 3. Naming Conventions

### Files

| Layer | Pattern | Example |
|-------|---------|---------|
| Routes | `{domain}_routes.py` | `user_routes.py`, `document_routes.py` |
| Models | `{domain}_model.py` | `user_model.py`, `academic_model.py` |
| Schemas | `{domain}_schema.py` | `user_schema.py`, `document_schema.py` |
| Repositories | `{domain}_repository.py` | `user_repository.py`, `vector_repository.py` |
| Services | `{domain}_service.py` | `user_service.py`, `academic_service.py` |
| Tasks | `{purpose}_tasks.py` | `ingestion_tasks.py`, `cleanup_tasks.py` |

### Classes

| Type | Pattern | Example |
|------|---------|---------|
| ORM Models | `PascalCase` noun | `User`, `Document`, `CourseOffering` |
| Pydantic Schemas | `{Model}{Action}` | `UserCreate`, `UserRead`, `DocumentUpdate` |
| Services | `{Domain}Service` | `UserService`, `AcademicService` |
| Repositories | `{Domain}Repository` | `UserRepository`, `DocumentRepository` |
| Abstract Interfaces | `I{Name}` | `IVectorRepo`, `IS3Storage` |
| Enums | `PascalCase` | `UserRole`, `DocFormat`, `ProcessingStatus` |

### Functions

| Context | Pattern | Example |
|---------|---------|---------|
| Route handlers | `verb_noun` | `register_user`, `get_document`, `list_departments` |
| Service methods | `verb_noun` | `authenticate_user`, `create_department`, `delete_course` |
| Repository methods | `verb_noun` | `get_by_email`, `create_document`, `update_status` |
| DI factories | `get_{service_name}` | `get_user_service`, `get_document_service` |

---

## 4. Dependency Injection Pattern

All services are injected into route handlers using FastAPI's `Depends()` system:

```python
# 1. Factory function at route-file level
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repo = UserRepository(db)
    return UserService(repo)

# 2. Route handler receives the injected service
@router.post("/register", response_model=StandardResponse[UserRead])
def register_user(user_in: UserCreate, service: UserService = Depends(get_user_service)):
    user = service.register_user(user_in)
    return StandardResponse(status="success", message="User registered", data=user)
```

**Chain**: `get_db()` → `Repository(db)` → `Service(repo)` → route handler

> **Rule**: Route handlers must NEVER instantiate repositories or call infrastructure directly. Always go through the service factory.

---

## 5. Standard API Response Format

All endpoints return a `StandardResponse` envelope:

```json
{
    "status": "success",
    "message": "Human-readable description of the result",
    "data": { ... }
}
```

**Schema** (from `src/schemas/response_schema.py`):

```python
class StandardResponse(BaseModel, Generic[T]):
    status: str        # "success" or "error"
    message: str       # Descriptive message
    data: T | None     # Typed payload (null on errors)
```

---

## 6. Authentication & Authorization

### Authentication Flow

1. Client sends `POST /api/v1/users/login` with `{ email, password }`.
2. Server validates credentials via `UserService.authenticate_user()`.
3. Server returns `access_token` + `refresh_token` (JWT) and sets an `access_token` HTTPOnly cookie.
4. Subsequent requests include the token via `Authorization: Bearer <token>` header **or** the HTTPOnly cookie.
5. `auth_middleware.get_current_user()` extracts and validates the JWT on each protected request.

### Authorization (RBAC)

Three roles exist: `ADMIN`, `PUBLISHER`, `STUDENT`.

```python
# Allow any authenticated user
user: User = Depends(get_current_user)

# Restrict to specific roles
user: User = Depends(require_role([UserRole.ADMIN]))
user: User = Depends(require_role([UserRole.ADMIN, UserRole.PUBLISHER]))
```

### Role Permissions Matrix

| Action | ADMIN | PUBLISHER | STUDENT |
|--------|-------|-----------|---------|
| Register user | ✅ | ✅ | ✅ |
| Create publisher account | ✅ | ❌ | ❌ |
| Login / Refresh | ✅ | ✅ | ✅ |
| Create department | ✅ | ❌ | ❌ |
| List / Get departments | ✅ | ✅ | ✅ |
| Create / Delete course | ✅ | ✅¹ | ❌ |
| Manage prerequisites | ✅ | ✅ | ❌ |
| Create / Delete offerings | ✅ | ✅ | ❌ |
| Manage faculty | ✅ | ✅ | ❌ |
| Get presigned upload URL | ✅ | ✅ | ❌ |
| Upload / Update / Delete documents | ✅ | ✅ | ❌ |
| View documents | ✅ | ✅ | ✅ |

¹ Publishers can create courses; only ADMIN can delete courses.

---

## 7. API Endpoint Reference

### 7.1 Root

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | ❌ | Health check — returns welcome message |
| `GET` | `/api` | ❌ | API root — returns welcome message |

---

### 7.2 Users & Authentication

**Prefix**: `/api/v1/users`  
**Tag**: `Users`

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| `POST` | `/api/v1/users/register` | ❌ | Public | Register a new student account |
| `POST` | `/api/v1/users/publishers` | ✅ | ADMIN | Create a publisher account |
| `POST` | `/api/v1/users/login` | ❌ | Public | Authenticate and receive JWT tokens |
| `POST` | `/api/v1/users/refresh` | ❌ | Public | Refresh access token using refresh token |

#### `POST /api/v1/users/register`

Register a new student user. Role is forced to `STUDENT` regardless of input.

**Request Body** (`UserCreate`):
```json
{
    "email": "student@kgpone.edu",
    "password": "securePassword123",
    "full_name": "John Doe"
}
```

**Response** `201 Created` (`StandardResponse[UserRead]`):
```json
{
    "status": "success",
    "message": "User registered successfully",
    "data": {
        "id": "uuid",
        "email": "student@kgpone.edu",
        "full_name": "John Doe",
        "role": "STUDENT",
        "is_active": true,
        "is_verified": false,
        "created_at": "2026-06-18T12:00:00Z",
        "updated_at": "2026-06-18T12:00:00Z"
    }
}
```

#### `POST /api/v1/users/publishers`

Create a publisher account. Requires ADMIN role.

**Request Body** (`UserCreate`):
```json
{
    "email": "publisher@kgpone.edu",
    "password": "securePassword123",
    "full_name": "Jane Publisher"
}
```

**Response** `201 Created` (`StandardResponse[UserRead]`)

#### `POST /api/v1/users/login`

Authenticate via email/password. Returns JWT tokens and sets `access_token` HTTPOnly cookie.

**Request Body** (`LoginRequest`):
```json
{
    "email": "student@kgpone.edu",
    "password": "securePassword123"
}
```

**Response** `200 OK` (`StandardResponse[TokenResponse]`):
```json
{
    "status": "success",
    "message": "Login successful",
    "data": {
        "access_token": "eyJhbGciOi...",
        "refresh_token": "eyJhbGciOi...",
        "token_type": "bearer"
    }
}
```

**Cookie Set**: `access_token` (HTTPOnly, max_age=1800s, samesite=lax)

#### `POST /api/v1/users/refresh`

Rotate both access and refresh tokens.

**Request Body** (`RefreshRequest`):
```json
{
    "refresh_token": "eyJhbGciOi..."
}
```

**Response** `200 OK` (`StandardResponse[TokenResponse]`)

---

### 7.3 Academic & Departments

**Prefix**: `/api/v1/academic`  
**Tag**: `Academic & Departments`

#### Departments

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| `POST` | `/api/v1/academic/departments` | ✅ | ADMIN | Create a department |
| `GET` | `/api/v1/academic/departments` | ✅ | Any | List all departments |
| `GET` | `/api/v1/academic/departments/{dept_id}` | ✅ | Any | Get department by ID |

##### `POST /api/v1/academic/departments`

**Request Body** (`DepartmentCreate`):
```json
{
    "code": "CSE",
    "name": "Computer Science and Engineering"
}
```

**Response** `201 Created` (`StandardResponse[DepartmentRead]`):
```json
{
    "status": "success",
    "message": "Department created successfully",
    "data": {
        "id": "uuid",
        "code": "CSE",
        "name": "Computer Science and Engineering",
        "created_at": "2026-06-18T12:00:00Z"
    }
}
```

#### Courses

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| `POST` | `/api/v1/academic/` | ✅ | ADMIN, PUBLISHER | Create a course |
| `GET` | `/api/v1/academic/` | ✅ | Any | List courses (optional `?department_id=`) |
| `GET` | `/api/v1/academic/{course_id}` | ✅ | Any | Get course by ID |
| `DELETE` | `/api/v1/academic/{course_id}` | ✅ | ADMIN | Soft-delete course (triggers cleanup) |

##### `POST /api/v1/academic/`

**Request Body** (`CourseCreate`):
```json
{
    "department_id": "uuid",
    "code": "CS101",
    "title": "Introduction to Computer Science",
    "description": "Fundamental programming concepts and algorithms.",
    "credits": 4
}
```

**Response** `201 Created` (`StandardResponse[CourseRead]`):
```json
{
    "status": "success",
    "message": "Course created successfully",
    "data": {
        "id": "uuid",
        "department_id": "uuid",
        "code": "CS101",
        "title": "Introduction to Computer Science",
        "description": "...",
        "credits": 4,
        "prerequisites": [],
        "created_at": "2026-06-18T12:00:00Z",
        "updated_at": "2026-06-18T12:00:00Z"
    }
}
```

#### Prerequisites

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| `POST` | `/api/v1/academic/{course_id}/prerequisites` | ✅ | ADMIN, PUBLISHER | Add prerequisite to course |
| `DELETE` | `/api/v1/academic/{course_id}/prerequisites/{prereq_id}` | ✅ | ADMIN, PUBLISHER | Remove prerequisite |

##### `POST /api/v1/academic/{course_id}/prerequisites`

**Request Body**:
```json
{
    "prerequisite_id": "uuid"
}
```

**Response** `201 Created` (`StandardResponse[CourseRead]`)

#### Course Offerings

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| `POST` | `/api/v1/academic/{course_id}/offerings` | ✅ | ADMIN, PUBLISHER | Create offering |
| `GET` | `/api/v1/academic/{course_id}/offerings` | ✅ | Any | List offerings for a course |
| `GET` | `/api/v1/academic/offerings/{offering_id}` | ✅ | Any | Get offering by ID |
| `DELETE` | `/api/v1/academic/offerings/{offering_id}` | ✅ | ADMIN, PUBLISHER | Delete offering |

##### `POST /api/v1/academic/{course_id}/offerings`

**Request Body** (`CourseOfferingCreate`):
```json
{
    "course_id": "uuid",
    "year": 2026,
    "semester": "AUTUMN"
}
```

**Response** `201 Created` (`StandardResponse[CourseOfferingRead]`):
```json
{
    "status": "success",
    "message": "Course offering created successfully",
    "data": {
        "id": "uuid",
        "course_id": "uuid",
        "year": 2026,
        "semester": "AUTUMN"
    }
}
```

#### Faculty

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| `GET` | `/api/v1/academic/offerings/{offering_id}/faculty` | ✅ | Any | List faculty for an offering |
| `POST` | `/api/v1/academic/offerings/{offering_id}/faculty` | ✅ | ADMIN, PUBLISHER | Add faculty to offering |
| `DELETE` | `/api/v1/academic/faculty/{faculty_id}` | ✅ | ADMIN, PUBLISHER | Remove faculty |

##### `POST /api/v1/academic/offerings/{offering_id}/faculty`

**Request Body** (`FacultyInfoCreate`):
```json
{
    "course_offering_id": "uuid",
    "name": "Dr. Amit Kumar",
    "email": "amit@kgp.edu",
    "role": "Professor",
    "office_hours": "Mon/Wed 2-4 PM"
}
```

**Response** `201 Created` (`StandardResponse[FacultyInfoRead]`):
```json
{
    "status": "success",
    "message": "Faculty added to offering successfully",
    "data": {
        "id": "uuid",
        "course_offering_id": "uuid",
        "name": "Dr. Amit Kumar",
        "email": "amit@kgp.edu",
        "role": "Professor",
        "office_hours": "Mon/Wed 2-4 PM",
        "created_at": "2026-06-18T12:00:00Z"
    }
}
```

---

### 7.4 Documents

**Prefix**: `/api/v1/documents`  
**Tag**: `Documents`

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| `POST` | `/api/v1/documents/presigned-url` | ✅ | ADMIN, PUBLISHER | Generate S3 presigned upload URL |
| `POST` | `/api/v1/documents/` | ✅ | ADMIN, PUBLISHER | Register document metadata & trigger ingestion |
| `GET` | `/api/v1/documents/offering/{offering_id}` | ✅ | Any | List documents for a course offering |
| `GET` | `/api/v1/documents/{document_id}` | ✅ | Any | Get document by ID |
| `PATCH` | `/api/v1/documents/{document_id}` | ✅ | ADMIN, PUBLISHER | Update document metadata (triggers re-ingestion) |
| `DELETE` | `/api/v1/documents/{document_id}` | ✅ | ADMIN, PUBLISHER | Soft-delete document (triggers cleanup) |

#### `POST /api/v1/documents/presigned-url`

Generates an S3 presigned PUT URL for direct browser-to-S3 uploads.

**Request Body** (`PresignedUrlRequest`):
```json
{
    "course_offering_id": "uuid",
    "filename": "lecture_notes.pdf",
    "content_type": "application/pdf"
}
```

**Response** `201 Created` (`StandardResponse[PresignedUrlResponse]`):
```json
{
    "status": "success",
    "message": "Presigned URL generated successfully",
    "data": {
        "upload_url": "https://s3.amazonaws.com/bucket/...",
        "file_key": "documents/CSE/CS101/2026_AUTUMN/user_uuid_file.pdf"
    }
}
```

#### `POST /api/v1/documents/`

Register document metadata after S3 upload completes. Triggers the async Celery ingestion pipeline.

**Request Body** (`DocumentCreate`):
```json
{
    "course_offering_id": "uuid",
    "title": "Algorithms Lecture 5",
    "description": "Graph algorithms and shortest paths",
    "parsing_instructions": "Focus on code blocks",
    "doc_type": "NOTES",
    "format": "PDF",
    "s3_key": "documents/CSE/CS101/2026_AUTUMN/file.pdf",
    "file_size_bytes": 1048576,
    "metadata_entries": [
        { "key": "chapter", "value": "5" }
    ]
}
```

**Response** `201 Created` (`StandardResponse[DocumentRead]`):
```json
{
    "status": "success",
    "message": "Document metadata saved successfully",
    "data": {
        "id": "uuid",
        "course_offering_id": "uuid",
        "uploader_id": "uuid",
        "title": "Algorithms Lecture 5",
        "description": "Graph algorithms and shortest paths",
        "parsing_instructions": "Focus on code blocks",
        "doc_type": "NOTES",
        "format": "PDF",
        "s3_key": "documents/CSE/CS101/2026_AUTUMN/file.pdf",
        "file_size_bytes": 1048576,
        "status": "PENDING",
        "qdrant_collection_id": null,
        "created_at": "2026-06-18T12:00:00Z",
        "updated_at": "2026-06-18T12:00:00Z",
        "metadata_entries": [
            { "id": "uuid", "document_id": "uuid", "key": "chapter", "value": "5" }
        ]
    }
}
```

#### `PATCH /api/v1/documents/{document_id}`

Update document metadata. If title/description/instructions change, triggers re-ingestion.

**Request Body** (`DocumentUpdate`):
```json
{
    "title": "Updated Title",
    "description": "Updated description",
    "parsing_instructions": "New instructions"
}
```

**Response** `200 OK` (`StandardResponse[DocumentRead]`)

#### `DELETE /api/v1/documents/{document_id}`

Soft-deletes the document and dispatches a Celery cleanup job to remove vectors, graph nodes, and S3 objects.

**Response** `200 OK` (`StandardResponse[DocumentRead]`)

---

## 8. Data Models Reference

### Enums

| Enum | Values | Used In |
|------|--------|---------|
| `UserRole` | `ADMIN`, `PUBLISHER`, `STUDENT` | `User.role` |
| `DocFormat` | `PDF`, `PPT`, `PPTX`, `DOC`, `DOCX` | `Document.format` |
| `ProcessingStatus` | `PENDING`, `PROCESSING`, `COMPLETED`, `FAILED` | `Document.status` |
| `SemesterType` | `AUTUMN`, `SPRING` | `CourseOffering.semester` |
| `DeletionStatus` | `NONE`, `PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED` | Soft-delete tracking |

### ORM Entity Relationship

```
Department 1──N Course 1──N CourseOffering 1──N Document
                  │                │                │
                  │ M──M           │ 1──N           │ 1──N
                  └─ Prerequisites └─ FacultyInfo   └─ DocumentMetadata

User 1──N Document
User 1──N RefreshToken
```

### Abstract Interfaces (`utils/interfaces.py`)

| Interface | Methods | Implementations |
|-----------|---------|-----------------|
| `IVectorRepo` | `search()`, `upsert()`, `delete_by_filter()` | `QdrantRepository` |
| `IS3Storage` | `upload()`, `generate_presigned_url()`, `download_file()`, `delete_file()` | `S3Storage` |
| `IGraphRepository` | `delete_document_nodes()`, `delete_course_nodes()` | `GraphRepository` |
| `IRetrievalService` | `retrieve_context()` | `RetrievalService` |

---

## 9. Error Handling

All errors are caught by global exception handlers and returned in a consistent format.

### Error Response Format

```json
{
    "status": "error",
    "message": "Human-readable error description",
    "data": null
}
```

### Exception Handler Mapping

| Exception Type | HTTP Status | Handler |
|---------------|-------------|---------|
| `HTTPException` | Varies (4xx/5xx) | `http_exception_handler` |
| `RequestValidationError` | `422 Unprocessable Entity` | `validation_exception_handler` |
| `ValueError` | `400 Bad Request` | `value_error_handler` |
| `IntegrityError` | `409 Conflict` | `integrity_error_handler` |
| `Exception` (generic) | `500 Internal Server Error` | `generic_exception_handler` |

| `500` | Server Error | Unhandled exception |

---

### 7.5 Query & Hybrid RAG

**Prefix**: `/api/v1/query`  
**Tag**: `Query & RAG`

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| `POST` | `/api/v1/query/ask` | ❌ | Public | Full Hybrid RAG pipeline for answering academic queries |
| `POST` | `/api/v1/query/search` | ❌ | Public | Vector-based semantic search for documents |

#### `POST /api/v1/query/ask`

Executes the intelligent routing pipeline: Intent Planning -> Retrieval (Vector + Graph) -> LLM Reranking -> LLM Answer Generation.

**Request Body** (`QueryRequest`):
```json
{
    "query": "What is the difference between DFS and BFS?",
    "course_code": "CS101"
}
```

**Response** `200 OK` (`StandardResponse[QueryResponse]`):
```json
{
    "status": "success",
    "message": "Query answered successfully",
    "data": {
        "answer": "DFS explores down a path fully before backtracking...",
        "citations": [...],
        "sources": [...],
        "intent": "compare",
        "backends_used": ["neo4j", "qdrant"]
    }
}
```

#### `POST /api/v1/query/search`

Forces a semantic search against the Qdrant vector database to return raw chunks.

**Request Body** (`QueryRequest`):
```json
{
    "query": "graph traversal techniques",
    "course_code": "CS101"
}
```

**Response** `200 OK` (`StandardResponse[List[SearchResult]]`)

---

## 10. MCP Server Integration

The backend includes a **Model Context Protocol (MCP)** server to allow external AI assistants (like Claude, Gemini, or ChatGPT Desktop) to natively interact with the KnowledgeOS platform.

### Starting the Server
```bash
cd backend
uv run src/mcp.py
```
Or use the MCP CLI to connect it directly:
```bash
mcp dev src/mcp.py
```

### Available Tools
The MCP server exposes the following tools to the AI:
- `list_departments()`: Fetch all departments
- `search_courses(query, department_code)`: Find courses
- `get_course_details(course_code)`: Retrieve syllabus and prerequisites
- `search_documents(query, course_code)`: Perform semantic search over course materials
- `answer_course_question(question, course_code)`: Run the full KnowledgeOS RAG pipeline for an answer
- `get_course_topics(course_code)`: Query the Neo4j graph for extracted topics

### Available Prompts
The MCP server provides standard prompts for guided AI interactions:
- `study_guide`: Creates a comprehensive course study guide based on catalog and graph data.
- `debug_prerequisites`: Helps a student discover what foundational knowledge they are missing.
