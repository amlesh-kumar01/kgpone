# KgpOne Architecture Overview

Welcome to the KgpOne project. This monorepo encompasses a sophisticated "Deep Learning Agent" architecture designed to guide students across academic topics, utilizing cutting-edge AI orchestration.

## The Big Picture
KgpOne bridges the gap in conceptual learning by deploying Autonomous Prerequisite Bridges. When a student asks about a complex topic, our system doesn't just answer—it analyzes prerequisites, traverses an academic knowledge graph, retrieves relevant vector-embedded educational materials, and synthesizes a complete learning lineage.

### Tech Stack
- **Frontend**: React 19, Vite, Tailwind CSS (JavaScript)
- **Backend**: Python 3.11+, FastAPI, LangChain, LangGraph, FastMCP
- **Infrastructure**: Docker Compose, PostgreSQL (Relational), Qdrant (Vector DB), Neo4j (Knowledge Graph), LocalStack/AWS S3 (Object Storage)
- **AI Models**: Gemini 1.5 Pro / Flash

### Repository Structure
- `/frontend/` - Contains the React Vite application.
- `/backend/` - Contains the FastAPI application and LangGraph agents.
- `/infra/` - Contains Terraform configurations and local scripts for AWS/LocalStack infrastructure.
- `/docs/` - Contains engineer guides and architectural documentation.

For detailed tasks and setup instructions specific to your domain, refer to the [Frontend Guide](frontend_guide.md) and [Backend Guide](backend_guide.md).
