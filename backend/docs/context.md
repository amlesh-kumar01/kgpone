# System Context & File Directory

This document provides a comprehensive mapping of all files in the backend workspace. Click on any file name to open it directly.

---

## Table of Contents

- **Root Configurations**
  - [alembic.ini](../alembic.ini)
  - [pyproject.toml](../pyproject.toml)
  - [Dockerfile](../Dockerfile)
  - [docker-compose.yml](../docker-compose.yml)
  - [README.md](../README.md)
  - [alembic/env.py](../alembic/env.py)
- **Application Core**
  - [src/main.py](../src/main.py)
  - [src/mcp.py](../src/mcp.py)
- **API Presentation Layer**
  - Middlewares
    - [auth_middleware.py](../src/api/middleware/auth_middleware.py)
    - [cors_middleware.py](../src/api/middleware/cors_middleware.py)
    - [request_logger.py](../src/api/middleware/request_logger.py)
    - [security_middleware.py](../src/api/middleware/security_middleware.py)
  - Routes
    - [course_routes.py](../src/api/routes/course_routes.py)
    - [document_routes.py](../src/api/routes/document_routes.py)
    - [user_routes.py](../src/api/routes/user_routes.py)
  - Exceptions
    - [handlers.py](../src/api/exceptions/handlers.py)
- **Configuration**
  - [settings.py](../src/config/settings.py)
- **Infrastructure Connectors**
  - [celery.py](../src/infrastructure/celery.py)
  - [database.py](../src/infrastructure/database.py)
  - [neo4j.py](../src/infrastructure/neo4j.py)
  - [qdrant.py](../src/infrastructure/qdrant.py)
  - [s3.py](../src/infrastructure/s3.py)
- **Database Models**
  - [user_model.py](../src/models/user_model.py)
  - [course_model.py](../src/models/course_model.py)
  - [document_model.py](../src/models/document_model.py)
  - [system_model.py](../src/models/system_model.py)
- **Data Repositories**
  - Postgres
    - [user_repository.py](../src/repositories/postgres/user_repository.py)
    - [course_repository.py](../src/repositories/postgres/course_repository.py)
    - [document_repository.py](../src/repositories/postgres/document_repository.py)
  - Qdrant Vector DB
    - [vector_repository.py](../src/repositories/qdrant/vector_repository.py)
  - AWS S3 Storage
    - [storage_repository.py](../src/repositories/s3/storage_repository.py)
  - Neo4j Graph DB
    - [graph_repository.py](../src/repositories/neo4j/graph_repository.py)
- **Pydantic Validation Schemas**
  - [user_schema.py](../src/schemas/user_schema.py)
  - [course_schema.py](../src/schemas/course_schema.py)
  - [document_schema.py](../src/schemas/document_schema.py)
  - [response_schema.py](../src/schemas/response_schema.py)
- **Business Logic Services**
  - [course_service.py](../src/services/academic/course_service.py)
  - [user_service.py](../src/services/auth/user_service.py)
  - [graph_builder_service.py](../src/services/graph/graph_builder_service.py)
  - [graph_query_service.py](../src/services/graph/graph_query_service.py)
  - [prerequisite_service.py](../src/services/graph/prerequisite_service.py)
  - RAG Engine
    - [answer_service.py](../src/services/rag/answer_service.py)
    - [citation_service.py](../src/services/rag/citation_service.py)
    - [rerank_service.py](../src/services/rag/rerank_service.py)
    - [retrieval_service.py](../src/services/rag/retrieval_service.py)
  - Ingestion Pipeline
    - [metadata_builder.py](../src/services/ingestion/metadata_builder.py)
    - [chunking/base.py](../src/services/ingestion/chunking/base.py)
    - [chunking/recursive_chunker.py](../src/services/ingestion/chunking/recursive_chunker.py)
    - [embedding/base.py](../src/services/ingestion/embedding/base.py)
    - [embedding/gemini_embedding.py](../src/services/ingestion/embedding/gemini_embedding.py)
    - [parser/base.py](../src/services/ingestion/parser/base.py)
    - [parser/llama_parser.py](../src/services/ingestion/parser/llama_parser.py)
    - [pipeline.py](../src/services/ingestion/pipeline.py)
    - [upload_manager/document_service.py](../src/services/ingestion/upload_manager/document_service.py)
- **Common Utilities**
  - [interfaces.py](../src/utils/interfaces.py)
  - [logger.py](../src/utils/logger.py)
- **Celery Tasks & Queues**
  - [app.py](../src/workers/app.py)
  - [tasks/cleanup_tasks.py](../src/workers/tasks/cleanup_tasks.py)
  - [tasks/ingestion_tasks.py](../src/workers/tasks/ingestion_tasks.py)

---

## Root Configurations

### [alembic.ini](../alembic.ini)
Configuration file for database migrations, specifying connection settings, execution transaction logs, format templates, and migration folder settings.

### [pyproject.toml](../pyproject.toml)
Project metadata definition file managed via `uv`, setting package requirements, versions, python constraints, and build tools.

### [Dockerfile](../Dockerfile)
Defines build steps to containerize the FastAPI backend service for production deployments.

### [docker-compose.yml](../docker-compose.yml)
Specifies background service layouts, providing a local Redis container to support asynchronous queue architectures.

### [README.md](../README.md)
General start guide containing project instructions, commands, requirements, and environment setups.

### [alembic/env.py](../alembic/env.py)
Database migration entry handler that runs SQLAlchemy schema alterations online or offline against the target database.

---

## Application Core

### [src/main.py](../src/main.py)
FastAPI main runtime config. It hooks up CORS, initializes security and logger middlewares, maps routes to versioned controllers, and applies global validation handlers.

### [src/mcp.py](../src/mcp.py)
Contains core stubs and hooks to interface with the Model Context Protocol (MCP) servers.

---

## API Presentation Layer

### Middlewares

#### [auth_middleware.py](../src/api/middleware/auth_middleware.py)
Extracts authorization cookies, decodes JWT parameters, resolves the logged-in user against the postgres backend, and handles Role-Based Access Control.

#### [cors_middleware.py](../src/api/middleware/cors_middleware.py)
Stores configuration constants and configurations determining cross-origin access allowances.

#### [request_logger.py](../src/api/middleware/request_logger.py)
Telemetry middleware intercepting request lifecycles to record metrics like response latency, targeting path, request source, and status codes.

#### [security_middleware.py](../src/api/middleware/security_middleware.py)
Appends headers protecting the API from common client-side threats including Clickjacking, script injection, and MIME types exploitation.

### Routes

#### [course_routes.py](../src/api/routes/course_routes.py)
Registers HTTP endpoints for departments, courses, offerings, and professors, returning standardized JSON responses.

#### [document_routes.py](../src/api/routes/document_routes.py)
FastAPI endpoints handling presigned uploads to S3, metadata edits, document versions, and asynchronous deletions.

#### [user_routes.py](../src/api/routes/user_routes.py)
Authentication routing for registration, cookie login, session refresh checks, and session revocation.

### Exceptions

#### [handlers.py](../src/api/exceptions/handlers.py)
Defines central response mapping for validation failures, duplicate keys, and generic server errors.

---

## Configuration

### [settings.py](../src/config/settings.py)
Pydantic configuration mapper parsing environment files (`.env`) into typed configuration constants across the application.

---

## Infrastructure Connectors

### [celery.py](../src/infrastructure/celery.py)
Initializes the Celery application engine connecting async workers to the Redis message queue.

### [database.py](../src/infrastructure/database.py)
Creates the SQLAlchemy DB engine connection and context manager for session generation.

### [neo4j.py](../src/infrastructure/neo4j.py)
Initializes drivers and clients managing transactions to the Neo4j Graph Database.

### [qdrant.py](../src/infrastructure/qdrant.py)
Handles startup client initialization and testing for Qdrant Cloud connectivity.

### [s3.py](../src/infrastructure/s3.py)
Creates and pools Boto3 connection clients connecting the service to the S3 bucket.

---

## Database Models

### [user_model.py](../src/models/user_model.py)
Declarative mapping defining columns, passwords, roles, and dates for User records.

### [course_model.py](../src/models/course_model.py)
SQLAlchemy schemas representing academic structures, supporting departments, courses, offerings, and soft deletes.

### [document_model.py](../src/models/document_model.py)
Schema definitions for documents (versions, states, soft deletes) and secondary key-value metadata collections.

### [system_model.py](../src/models/system_model.py)
Auditing schema models defining the soft-delete state enum and the background asynchronous Cleanup Job task table.

---

## Data Repositories

### Postgres

#### [user_repository.py](../src/repositories/postgres/user_repository.py)
Direct database interfaces for inserting, querying, and updating system user records.

#### [course_repository.py](../src/repositories/postgres/course_repository.py)
SQL queries and operations mapping department structures and course offering models.

#### [document_repository.py](../src/repositories/postgres/document_repository.py)
CRUD operations modifying document upload status records and tracking soft-deleted entities.

### Qdrant Vector DB

#### [vector_repository.py](../src/repositories/qdrant/vector_repository.py)
Coordinates collection creations, registers vector indexes, inserts embedded chunks, and runs metadata-filtered searches on Qdrant.

### AWS S3 Storage

#### [storage_repository.py](../src/repositories/s3/storage_repository.py)
Produces presigned AWS file upload targets, validates uploaded document integrity, and executes file deletions.

### Neo4j Graph DB

#### [graph_repository.py](../src/repositories/neo4j/graph_repository.py)
Executes Cypher scripts organizing prerequisites, entities, and topics within Neo4j.

---

## Pydantic Validation Schemas

### [user_schema.py](../src/schemas/user_schema.py)
Request and response constraints for user registration, user logins, and token responses.

### [course_schema.py](../src/schemas/course_schema.py)
Input/Output formats representing academic departments, new course entries, and assignable faculty.

### [document_schema.py](../src/schemas/document_schema.py)
Input formats for updating document metadata parameters, presigned configurations, and status responses.

### [response_schema.py](../src/schemas/response_schema.py)
Defines the standard API response format `StandardResponse` used across all controllers to maintain a consistent output layout.

---

## Business Logic Services

### [course_service.py](../src/services/academic/course_service.py)
Handles business constraints for departments, faculty roles, and course records, registering background soft deletion tasks.

### [user_service.py](../src/services/auth/user_service.py)
Coordinates user operations, wrapping bcrypt encryption for user passwords and managing JWT token issuance.

### [graph_builder_service.py](../src/services/graph/graph_builder_service.py)
Extracts academic entities from ingested texts to append new nodes and relationships inside Neo4j.

### [graph_query_service.py](../src/services/graph/graph_query_service.py)
Retrieves prerequisite models and concept connections from the graph db layer.

### [prerequisite_service.py](../src/services/graph/prerequisite_service.py)
Processes course prerequisites and outlines curricular path recommendations for students.

### RAG Engine

#### [answer_service.py](../src/services/rag/answer_service.py)
Synthesizes responsive answers by compiling relevant vector segments into an LLM context.

#### [citation_service.py](../src/services/rag/citation_service.py)
Builds source links, linking sections to source documents to support verifiable RAG footnotes.

#### [rerank_service.py](../src/services/rag/rerank_service.py)
Re-evaluates and ranks search results using Cross-Encoders to improve prompt contexts.

#### [retrieval_service.py](../src/services/rag/retrieval_service.py)
Combines semantic keyword vector matches and relational graph data to locate documents.

### Ingestion Pipeline

#### [metadata_builder.py](../src/services/ingestion/metadata_builder.py)
Builds flattened, Qdrant-indexable payloads containing database relations (course, uploader, custom metadata) to allow payload filtering.

#### [chunking/base.py](../src/services/ingestion/chunking/base.py)
Interface constraints outlining text-splitter implementations.

#### [chunking/recursive_chunker.py](../src/services/ingestion/chunking/recursive_chunker.py)
Divides source texts into structured pieces using markdown header definitions.

#### [embedding/base.py](../src/services/ingestion/embedding/base.py)
Interface constraints outlining document embedding methods.

#### [embedding/gemini_embedding.py](../src/services/ingestion/embedding/gemini_embedding.py)
Computes vector arrays from text chunks via Google's `text-embedding-004` APIs.

#### [parser/base.py](../src/services/ingestion/parser/base.py)
Interface constraints defining raw document text parsing classes.

#### [parser/llama_parser.py](../src/services/ingestion/parser/llama_parser.py)
Parses uploaded files via LlamaParse, preserving tables, figures, and structural markup.

#### [pipeline.py](../src/services/ingestion/pipeline.py)
Sequences documents through raw parsing, chunk splitters, vector calculation, and Qdrant saves.

#### [upload_manager/document_service.py](../src/services/ingestion/upload_manager/document_service.py)
Manages database states, handling uploads, soft-deletes, metadata updates, and Celery tasks triggering.

---

## Common Utilities

### [interfaces.py](../src/utils/interfaces.py)
Declares abstract contracts (e.g. `IVectorRepo`, `IStorageRepo`) to isolate dependencies.

### [logger.py](../src/utils/logger.py)
Bootstraps global logs formatting, capturing outputs for console and tracking streams.

---

## Celery Tasks & Queues

### [app.py](../src/workers/app.py)
Registers tasks and routes payload parameters to background Celery queues.

### [tasks/cleanup_tasks.py](../src/workers/tasks/cleanup_tasks.py)
Asynchronously removes vector payloads, graph DB nodes, and S3 objects for soft-deleted documents or courses.

### [tasks/ingestion_tasks.py](../src/workers/tasks/ingestion_tasks.py)
Asynchronous pipeline processor. It downloads documents from S3, extracts text using LLM parsers, chunks the output, embeds paragraphs, and logs them into Qdrant.
