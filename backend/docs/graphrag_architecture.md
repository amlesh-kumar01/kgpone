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

When a user asks a question via the `/api/v1/query/ask` endpoint, the system follows a 4-step process:

### Step 1: Query Planning
The `PlannerService` uses an LLM to analyze the user's intent. It classifies the query (e.g., `semantic_search`, `prerequisites`, `compare`, `concept_search`) and determines which backend databases (PostgreSQL, Qdrant, Neo4j) are needed to answer it.

### Step 2: Hybrid Retrieval
The `RetrievalService` dynamically coordinates data retrieval based on the `QueryPlan`:
*   **Vector Retrieval**: If semantic search is needed, it fetches top relevant chunks from Qdrant based on the user's query embedding.
*   **Graph Retrieval**: If structured knowledge is needed (e.g., prerequisite checking), it executes Cypher queries against Neo4j to find paths or related entities. These graph facts are converted into "synthetic chunks" to provide context to the LLM.

### Step 3: Reranking
The `RerankService` takes all retrieved chunks (both vector and graph) and evaluates them using an LLM to assign a relevance score between 0.0 and 1.0. A diversity penalty is applied to chunks from the same document to ensure a broad context. The chunks are sorted by their final score, and the top N are kept.

### Step 4: Answer Generation & Citations
The `CitationService` formats the provenance metadata for the top chunks (e.g., `[CIT-1]`). The `AnswerService` then passes the query, the reranked chunks, and the citation metadata to the LLM to generate the final, grounded response.

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
