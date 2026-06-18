# Project Information: KgpOne Backend

## Overview
KgpOne is a comprehensive academic knowledge management system and backend API. It leverages modern asynchronous Python (FastAPI), deep learning-based PDF ingestion (LlamaParse), dense vector embeddings (Gemini), and a robust relational database (PostgreSQL) to serve as the intelligence layer for course materials.

## Core Technologies
- **Framework**: FastAPI (Asynchronous, High-Performance)
- **Dependency Management**: `uv`
- **Database (Relational)**: PostgreSQL (via SQLAlchemy 2.0 & Alembic)
- **Database (Vector)**: Qdrant
- **Message Broker & Background Tasks**: Celery & Redis
- **Cloud Storage**: AWS S3 (or LocalStack for local dev)
- **AI Integration**:
  - `llama-parse` (Vision LLM parsing of PDFs)
  - `google-genai` (Gemini embeddings generation)
  - `langchain-text-splitters` (Markdown-aware chunking)

## Key Features
1. **Role-Based Access Control (RBAC)**: Secure endpoints protected by JWT authentication with rotating refresh tokens, scoping access across `STUDENT`, `TA`, `PROFESSOR`, and `ADMIN` roles.
2. **Metadata-Driven Vector Search**: Highly optimized semantic search queries executed directly on Qdrant, filtering securely using pre-indexed payload schemas mapped from PostgreSQL.
3. **Modular Background Ingestion**: Uploaded PDFs are stored in S3, and asynchronously processed by Celery. The pipeline splits tables, maths, and texts, embeds them, and persists them into Qdrant.
