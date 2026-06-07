# Backend Engineer Guide

Welcome to the KgpOne Backend team! You are responsible for engineering the API layer and the deep multi-turn agent workflows using Python.

## Tech Stack
- **Web API**: FastAPI (Python 3.11+)
- **AI Orchestration**: LangChain & LangGraph
- **Agent Interface**: FastMCP (Model Context Protocol wrapper)
- **Databases**: PostgreSQL (Relational), Qdrant (Vector), Neo4j (Graph)
- **Storage**: Boto3 (AWS S3 / LocalStack)

## Project Structure (`/backend/src/`)
We follow SOLID principles, keeping the Domain Core agnostic of the frameworks.
- `core/`: Abstract interfaces, entities, and LangGraph workflow states.
- `infrastructure/`: Concrete implementations (Qdrant clients, Neo4j traversals, Boto3 S3 connections).
- `api/`: FastAPI web layer (Dependencies, Routers, Middleware).
- `mcp_server/`: Headless agent wrappers for FastMCP interoperability.

## Your Immediate Tasks

1. **Implement "Deep Agents" via LangGraph**:
   - **Task**: In `core/services.py`, construct the State Graph for the Autonomous Prerequisite Bridge.
   - **Flow**: 
     1. *Evaluate Query*: Analyze user input against course scope.
     2. *Conditional Router*: Detect conceptual gaps.
     3. *Graph Traversal*: Query Neo4j to find prerequisite topics.
     4. *Vector Retrieval*: Fetch matching context from Qdrant/S3.
     5. *Synthesize*: Loop back and formulate the learning lineage.

2. **Data Layer Adapters**:
   - **Task**: Implement the abstract interfaces defined in `core/interfaces.py` inside the `infrastructure/` folder.
   - Flesh out `vector_db.py` (Qdrant search), `graph_db.py` (Neo4j queries), and `s3_storage.py` (Boto3 integration with LocalStack).

3. **PDF Parsing Engine**:
   - **Task**: Build the layout parsing engine in `infrastructure/parser.py` capable of chunking structural PDFs before sending them to Qdrant for embedding.

4. **FastMCP Integration**:
   - **Task**: Complete the tool registration in `mcp_server/tools.py` so that external model context protocols can seamlessly interface with our LangChain logic.

## Running Locally
Ensure `docker-compose up -d` is running at the root.
```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload
```
