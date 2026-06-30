# KnowledgeOS GraphRAG Architecture

This document describes the Hybrid GraphRAG architecture implemented in KnowledgeOS.

## Overview

KnowledgeOS uses a hybrid approach to Retrieval-Augmented Generation (RAG) that combines vector semantic search (Qdrant) with a structured knowledge graph (Neo4j). This allows the system to answer complex queries about curriculum, prerequisites, and course materials accurately.

## 1. Data Ingestion Pipeline

When a document is uploaded via the S3 presigned URL, a Celery background task orchestrates the ingestion pipeline (`IngestionPipeline`).

The pipeline consists of:
1.  **Parsing**: Documents (PDF, DOCX, etc.) are converted to structured markdown via LlamaParse.
2.  **Chunking**: The markdown is split into logical semantic chunks using `RecursiveChunker`.
3.  **Embedding**: Chunks are embedded using the `GeminiEmbedder`.
4.  **Vector Storage**: The embedded chunks and their metadata are upserted into **Qdrant**.
5.  **Entity Extraction (Knowledge Graph)**: In parallel, chunks are processed by the `GeminiEntityExtractor`. The LLM identifies educational entities (Topics, Concepts, Algorithms, Formulas, Books, Papers) and their relationships.
6.  **Graph Synchronization**: The `GraphBuilderService` merges the extracted entities and relationships into the **Neo4j** graph, linking them to the appropriate `Course` and `Document` nodes.

## 2. The Knowledge Graph (Neo4j)

The Neo4j database serves two primary purposes:
1.  **Academic Structure**: It mirrors the PostgreSQL academic hierarchy (Departments -> Courses).
2.  **Educational Concepts**: It stores the concepts and topics extracted from course documents, providing a semantic web of knowledge.

**Key Node Labels:**
*   `Department`, `Course`
*   `Topic`, `Concept`, `Algorithm`, `Formula`, `Technology`, `Book`, `Paper`

**Key Relationships:**
*   `(:Course)-[:PREREQUISITE]->(:Course)`
*   `(:Course)-[:COVERS]->(:Topic)`
*   `(:Concept)-[:DEPENDS_ON]->(:Concept)`

## 3. Intelligent Query Routing & Retrieval

## 3. Intelligent Query Routing & Retrieval

When a user asks a question via the `/api/v1/query/ask` endpoint, the system follows a 5-step process optimized for low latency (sub-second Time-To-First-Token):

### Step 0: Semantic Caching (Redis)
The `SemanticCacheService` checks Redis for previously answered identical queries. It hashes the first 64 dimensions of the query embedding to find a match. If a cache hit occurs, the pipeline bypasses retrieval and returns the cached answer and citations instantly (<5ms).

### Step 1: NLP Query Planning
The `NLPPlannerService` uses a lightweight, deterministic TF-IDF + SVM model to analyze the user's intent locally (no LLM required, <10ms). It classifies the query (e.g., `semantic_search`, `prerequisites`, `compare`, `concept_search`), extracts entities via regex and noun-chunking, and determines the required backend databases.

### Step 2: Parallel Hybrid Retrieval
The `RetrievalService` dynamically coordinates data retrieval based on the `QueryPlan`:
*   **Parallel Execution**: It fires off requests to Qdrant (vector search), Neo4j (graph traversal), and PostgreSQL concurrently using `asyncio.gather()`.
*   **Reciprocal Rank Fusion (RRF)**: Once all backends return their chunks, the disparate scores (cosine similarity vs. graph confidence) are unified and merged into a single ranked list using the RRF algorithm.

### Step 3: Cross-Encoder Reranking
The `CrossEncoderRerankService` evaluates the top merged chunks. It uses the HuggingFace Serverless Inference API (e.g., `BAAI/bge-reranker-v2-m3`) to process query-chunk pairs in a single batched HTTP request (~200ms). It also applies an 80% text overlap deduplication (context compression) and diversity penalties for chunks from the same document.

### Step 4: Answer Generation & Citations
The `CitationService` formats the provenance metadata for the top chunks (e.g., `[CIT-1]`). The `AnswerService` then passes the query, the reranked chunks, and the citation metadata to the LLM. This is the **only** LLM call in the entire query pipeline, used strictly to synthesize the final grounded response.

## 4. MCP Server Integration

The backend includes a standalone FastMCP server (`src/mcp/server.py`). This allows external AI assistants (like Claude Desktop) to connect natively to the KnowledgeOS platform.

The MCP server exposes powerful tools to the AI:
*   `list_departments`
*   `search_courses`
*   `get_course_details`
*   `search_documents`
*   `answer_course_question`
*   `get_course_topics`

This allows AI assistants to perform complex academic research using the underlying GraphRAG infrastructure on behalf of the user.
