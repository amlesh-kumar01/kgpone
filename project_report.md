# KgpOne — Comprehensive Technical Project Report

> **System Codename**: KgpOne
> **Context**: Academic AI Platform for Document-Driven Student Learning
> **Stack**: FastAPI · Celery · Docling · GLiNER · Qdrant · Neo4j · PostgreSQL · Redis · React · Infinity Embedding Server
> **Report Date**: August 2026

---

## 1. Executive Summary

KgpOne is a full-stack AI-powered academic preparation platform designed to help students deeply learn from their course documents. A student or administrator uploads a PDF (lecture slides, past-year question papers, notes, syllabi), and the platform automatically runs a multi-stage intelligent ingestion pipeline that parses, understands, and indexes the document into a knowledge graph and a vector store. Students can then ask natural-language questions and receive grounded, citation-backed answers, or trigger on-demand AI generation of formula sheets, topic summaries, and practice question banks — all in beautifully formatted Markdown.

The architecture is deliberately layered:
- A **document intelligence layer** that deeply understands structure
- A **knowledge layer** that extracts entities and relationships
- A **retrieval layer** that fuses vector similarity with graph traversal
- An **analysis layer** that uses LLMs to synthesize study materials

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              React SPA Frontend (Vite + shadcn/ui)           │
│   Dashboard · Pipeline · Chat · AnalysisStudio · Admin       │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTP/REST (Axios)
┌─────────────────────▼────────────────────────────────────────┐
│         FastAPI Backend  (Python 3.12 + uvicorn)             │
│  Routers: users, academic, documents, chat, ingestion,       │
│           analysis, analysis_generation, MCP                 │
│  Middleware: CORS, SecurityHeaders, RequestLogger            │
└──────┬──────────┬──────────────┬──────────────┬─────────────┘
       │          │              │              │
  PostgreSQL   AWS S3        Redis         MCP SSE /mcp/sse
  (relational) (artifacts)   (broker +
                              cache)
                                │
                     ┌──────────▼──────────┐
                     │   Celery Worker     │
                     │  8-stage Pipeline   │
                     └──────────┬──────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
           Neo4j             Qdrant           Infinity
          (graph)           (vector)       (GPU embedder
                                           + reranker)
```

---

## 3. Academic Domain Model

The platform models a full academic hierarchy in **PostgreSQL** via SQLAlchemy:

```
OrganizationalUnit  (e.g., "School of Engineering")
      └── StudyUnit   (e.g., "CS3001 — Algorithms")  [self-referential prerequisites]
              └── Document  (PDF/PPTX/DOCX upload)
                    └── IngestionJob  (one row per pipeline stage)
```

| Model | Key Fields |
|---|---|
| `OrganizationalUnit` | `code`, `name`, soft-delete |
| `StudyUnit` | `code`, `name`, `credits`, `prerequisites[]` (self-join) |
| `Document` | `title`, `doc_type`, `format`, `s3_prefix`, `status`, `artifacts` (JSONB), `version` |
| `IngestionJob` | `document_id`, `stage` enum, `status` enum, `output_s3_key`, timestamps |

The `artifacts` JSONB column on `Document` acts as a live key index, storing S3 paths for each stage's output artifact as they are produced in real-time.

---

## 4. The Document Ingestion Pipeline

This is the heart of the system. When a document is uploaded, a Celery chain is automatically triggered. Every task is declared with `autoretry_for=(Exception,), max_retries=3` — making the pipeline **idempotent and retry-proof**. Any stage can be manually restarted from the UI; doing so automatically cascade-resets all downstream stages.

### Execution Order

```
PARSE → AST → ENTITY → RELATION → GRAPH → CHUNK → EMBED → MANIFEST
```

> **Critical design decision**: Knowledge extraction (ENTITY/RELATION/GRAPH) runs **before** chunking. This lets the chunker embed entity anchor IDs directly into each chunk's metadata, dramatically improving the semantic precision of downstream vector retrieval.

---

### Stage 1 — PARSE

**Task**: `parse_document_task`

**Why**: Every ingestion starts by converting the raw binary document into a structured, machine-readable intermediate representation.

**How**:
1. Downloads the original file from S3 to a temp path.
2. Attempts parsing with **Docling** (IBM Research's open-source deep document AI). Docling uses GPU-accelerated vision-language models for layout analysis, table structure recognition, figure captioning, and reading-order detection.
3. Docling's output is immediately mapped to the **Canonical AST** schema and saved to S3 as `canonical/canonical.json`.
4. All embedded base64 images in Docling's output are extracted, uploaded as individual PNG assets to S3, and replaced with their S3 keys.
5. **Fallback**: If Docling fails, the system automatically falls back to **LlamaParse** (cloud API) via an async call.

**S3 Artifacts Produced**:
- `parsers/docling.json` — raw Docling output
- `canonical/canonical.json` — structured canonical AST
- `document.md` — native Markdown export of the document
- `pages/001.png` ... `pages/NNN.png` — page renders
- `pages_manifest.json` — page dimensions

---

### Stage 2 — AST (Canonical Abstract Syntax Tree)

**Task**: `build_canonical_ast_task`

**Why**: A vendor-neutral Canonical AST is essential so all downstream stages work against one stable schema, regardless of which parser ran in Stage 1.

**How**:
- If Docling already produced `canonical.json` (the common path), this stage is a **smart no-op** — it detects the file and skips.
- If Stage 1 used LlamaParse, `ASTBuilder` converts the LlamaParse JSON to a `CanonicalDocument` Pydantic model.

**Canonical AST Schema** (`ast_schema.py`):
```
CanonicalDocument
  ├── provenance: ParserProvenance  (parser, quality score, timestamp)
  ├── toc: List[Dict]
  └── nodes: List[ASTNode]
        ├── id, type (NodeType), title, level
        ├── parent_id, children[]
        ├── text_content, reading_order
        └── source: NodeSource (page_start, page_end, bbox, confidence)
```

`NodeType` covers 30+ semantic types: `CHAPTER`, `SECTION`, `PARAGRAPH`, `TABLE`, `FIGURE`, `EQUATION`, `FORMULA`, `QUESTION`, `ANSWER`, `ALGORITHM`, `CODE_BLOCK`, `THEOREM`, `PROOF`, `DEFINITION`, `EXAMPLE`, and more.

---

### Stage 3 — ENTITY (Knowledge Extraction)

**Task**: `extract_entities_task`

**Why**: To build a semantic layer above raw text — identifying *what concepts, algorithms, tools, and methods* the document discusses, and *where* they appear.

**How — Two-Pass Hybrid Extraction**:

**Pass 1 — GLiNER** (Generalist Linear NER):
- Loads `BAAI/GLiNER-multitask` model locally via `NLPModelFactory`.
- Labels: `Concept`, `Algorithm`, `Dataset`, `Metric`, `Author`, `Tool`, `Task`, `Methodology`.
- Processes every `ASTNode` in the canonical document with provenance tracking (`source_node_id`, `source_page`).
- Naive deduplication by `(text.lower(), label)` before LLM merge.

**Pass 2 — LLM Extraction**:
- Sends the top 10 longest paragraphs to the configured LLM.
- Extracts higher-level categories: `topics`, `concepts`, `algorithms`, `technologies` — enriched with natural-language descriptions.
- Merged into the main entity list with `confidence: 0.9`.

**Why GLiNER over spaCy alone?** spaCy's NER is trained on news corpora and fails on academic terminology. GLiNER is zero-shot — it accepts any custom labels at inference time, requiring no fine-tuning.

**S3 Output**: `knowledge/entities.json`

---

### Stage 4 — RELATION (Relationship Extraction)

**Task**: `extract_relations_task`

**Why**: Raw entities alone don't capture *how concepts relate*. Relations form the edges of the knowledge graph and enable semantically-aware graph retrieval.

**How — Two Strategies**:

**Strategy 1 — Structural Rules (confidence 0.9)**:
- Recursively traverses the AST tree.
- A `SECTION` heading containing entity A, whose child paragraph contains entity B → infers `A EXPLAINS B`.
- High-confidence because the document's own hierarchy encodes intent.

**Strategy 2 — spaCy Sentence Co-occurrence (confidence 0.6)**:
- Loads `en_core_web_sm` via `NLPModelFactory`.
- For each AST node with ≥2 entities, runs spaCy sentence splitting.
- Two entities co-occurring in the same sentence → `RELATED_TO` relation.

**S3 Output**: `knowledge/relations.json` — list of `{source, target, relation, confidence, method}`

---

### Stage 5 — GRAPH (Neo4j Knowledge Graph)

**Task**: `build_neo4j_task`

**Why**: Storing entities and relations as a property graph enables structured, relationship-aware queries that go beyond keyword or vector similarity — e.g., "what concepts does Section 3 explain?"

**How**: Connects to **Neo4j AuraDB** and persists entity nodes and relationship edges from Stages 3–4. Currently transitioning to full graph-write implementation; the RAG retriever already consumes the graph via `Neo4jRepo`.

---

### Stage 6 — CHUNK (Semantic Chunking)

**Task**: `build_chunks_task`

**Why**: LLMs have finite context windows. The document must be divided into small, semantically coherent, retrievable units that can be vectorized individually.

**How** (`ASTChunker`):
- Reads `canonical.json`, `entities.json`, and `formulas.json` from S3.
- Builds lookup maps: `node_id → Set[entity_names]` and `node_id → Set[formula_ids]`.
- Traverses the AST tree, accumulating leaf-node text (paragraphs, list items) into the current chunk buffer.
- When the buffer exceeds `max_chunk_tokens` (≈500 tokens, estimated as `len/4`) or hits a section boundary → **flushes** the chunk.
- Each chunk carries rich metadata: `heading_path`, `section_id`, `chapter_id`, `concept_ids[]`, `formula_ids[]`, `page_numbers[]`, `source_node_ids[]`.

This **entity-aware chunking** means every chunk knows which academic concepts it covers — enabling concept-filtered retrieval in the RAG engine.

**S3 Output**: `retrieval/chunks.json`

---

### Stage 7 — EMBED (Vector Indexing)

**Task**: `index_qdrant_task`

**Why**: Semantic search requires dense vector representations stored in a vector database for approximate nearest-neighbour retrieval.

**How**:
1. Reads all chunks from S3.
2. Calls `LLMEmbedder.embed(texts)` → posts to the **Infinity Embedding Server** (GPU-hosted `BAAI/bge-small-en-v1.5`, OpenAI-compatible API on port 7997).
3. **Before upserting: deletes all existing Qdrant vectors for this `document_id`** — making retries safe with zero orphan vectors.
4. Upserts `(vector, metadata)` pairs to the `documents` Qdrant collection. Each vector's payload includes `document_id`, `study_unit_code`, `document_type`, `chunk_id`, `text`, `heading_path`, `concept_ids[]`, `formula_ids[]`.

---

### Stage 8 — MANIFEST (Finalization)

**Task**: `finalize_manifest_task`

**Why**: Produce a final completion record, update document status, and generate a human-readable AI-powered study summary.

**How**:
1. Reads chunk and entity counts from S3.
2. Builds `manifest.json` with stats (chunk count, entity count, document ID, title, timestamp).
3. Calls the configured LLM to write a **3-paragraph study guide summary** from the first 5 chunks — output is Markdown.
4. Saves `summary.md` to `{s3_prefix}/summary.md`.
5. Updates `Document.status = COMPLETED` in PostgreSQL.
6. Stores the `summary` S3 key in `Document.artifacts` JSONB.

---

## 5. The Infinity Embedding Server

A dedicated Python service (`infinity/main.py`) runs a self-hosted GPU embedding server using the `infinity-emb` library. It loads **two models simultaneously** on the CUDA device:

| Model | Purpose | Approx. VRAM |
|---|---|---|
| `BAAI/bge-small-en-v1.5` | Dense bi-encoder embeddings (384-dim) | ~500 MB |
| `BAAI/bge-reranker-v2-m3` | Cross-encoder reranking | ~1.5 GB |

The server exposes an **OpenAI-compatible REST API** on port `7997`. The `LLMFactory` uses `langchain_openai.OpenAIEmbeddings` pointed at this URL — meaning the codebase is identical for local GPU and cloud OpenAI embedding paths.

**Why GPU?** Embedding 15 chunks on CPU ≈ 30 seconds. On GPU ≈ under 1 second. At query time, even a 200ms embedding call materially degrades chat UX.

---

## 6. Hybrid RAG Query Engine

When a student types a question, the following pipeline executes in real-time:

### Step 1 — Query Planning
- Classifies intent: `conceptual`, `formula`, `problem`, `historical`, `prerequisite`, `syllabus`, `general`.
- Determines which backends to query: `qdrant`, `neo4j`, `postgresql`.
- Scopes the query to a `study_unit_code`.

### Step 2 — Parallel Hybrid Retrieval
All backend retrievals run **concurrently** via `asyncio.gather()`:

| Backend | What it does |
|---|---|
| **Qdrant** | Embeds query → ANN search → returns top-K chunks filtered by study unit |
| **Neo4j** | Graph traversal via `EXPLAINS`/`RELATED_TO` edges → related content |
| **PostgreSQL** | Structured metadata queries (prerequisites, syllabus topics) |

Results are merged using **Reciprocal Rank Fusion (RRF)**: `score = Σ 1/(k + rank_i)`.

> **Why RRF over score normalization?** Different backends produce incomparable score scales (cosine distance vs. path depth vs. text match score). RRF uses only *rank position* — making it robust to heterogeneous scales with no calibration needed.

### Step 3 — Cross-Encoder Reranking
- Top 30 fused candidates → **BGE Cross-Encoder** on the Infinity server.
- Cross-encoders process `[QUERY] [SEP] [CHUNK]` simultaneously — true contextual relevance, not just vector proximity.
- Applied to only 30 pre-filtered candidates to keep latency bounded.
- Fallback: lexical boost scoring if Infinity is unavailable.

### Step 4 — Semantic Cache
- Before retrieval: checks a **Redis-backed semantic cache** keyed by query embedding cosine similarity.
- Cache TTL configurable (default 1 hour), scoped per `study_unit_id`.

### Step 5 — Answer Generation
- Top-5 reranked chunks + citation metadata → LLM.
- Synthesizes a grounded academic answer with inline `[CIT-N]` citations.
- Citations trace back to document title, study unit, and exact text snippet.

---

## 7. Analysis Studio

Manually-triggered AI content generation on top of fully-ingested documents. Accessible per-document or across an entire Study Unit.

### Generation Types

| Type | Output |
|---|---|
| `FORMULA_SHEET` | Full formula compilation with variable definitions — Markdown |
| `SUMMARY` | Hierarchical academic summary by document section |
| `QUESTION_BANK` | Practice questions (MCQ, short answer) from document content |
| `COMPARISON` | Side-by-side concept comparison across multiple documents |
| `QUIZ` | Interactive quiz with answer keys |
| `FORMULA_REVISION` | Topic-specific formula revision cards |

**Generation Flow**:
1. User selects type, optionally provides a custom prompt or topic filters.
2. `AnalysisGenerationTask` Celery task dispatched.
3. Task loads `canonical.json` + `chunks.json` + `entities.json` from S3.
4. Structured LLM prompt crafted with generation-type-specific instructions.
5. LLM output (Markdown) saved to S3 at `analysis/{type}/{analysis_id}.md`.
6. Presigned S3 URL returned; frontend renders in rich Markdown viewer.
7. All past generations stored persistently as a history list.

---

## 8. MCP Server Integration

The backend mounts an **MCP (Model Context Protocol) server** at `/mcp/sse`, making KgpOne's knowledge accessible to any MCP-compatible AI agent (Claude Desktop, MCP Inspector, etc.).

**Tools**: `search_documents`, `get_document_entities`, `get_study_unit_info`, `list_documents`

**Prompts**: Pre-configured study-session, concept-explanation, and exam-preparation prompts.

This makes KgpOne extensible beyond its own frontend — external AI agents can use it as a knowledge retrieval tool.

---

## 9. Frontend Architecture

Built with **React + Vite**, styled with **TailwindCSS**, using **shadcn/ui** component primitives.

**Design System**: "Illuminated Heritage"
- Primary: `#000b21` (deep navy)
- Accent: `#fed488` (warm gold / secondary-container)
- Typography: Manrope (sans), Libre Caslon Text (serif), Hanken Grotesk (mono)

### Key Pages

| Page | Role |
|---|---|
| `Dashboard.jsx` | System overview, processing queue, stats |
| `Documents.jsx` | Upload, list, filter documents by type |
| `DocumentPipeline.jsx` | Live pipeline inspector — 4-phase view with per-stage restart |
| `Chat.jsx` | Student RAG chat with citation rendering |
| `AnalysisStudio.jsx` | Per-document AI generation (formula sheets, summaries, questions) |
| `StudyUnitAnalysisStudio.jsx` | Cross-document analysis across an entire course |
| `AcademicManagement.jsx` | Admin: org units, offerings, study units |
| `Users.jsx` | RBAC user management (ADMIN / PUBLISHER / STUDENT) |
| `SharedChat.jsx` | Shareable chat sessions via public link |
| `Marketplace.jsx` | Study unit discovery |

### Pipeline UI Highlights

- **4 phase groups**: Parse · Knowledge · Indexing · Completion
- **Real-time polling** (5-second interval while RUNNING/PENDING)
- **Per-stage restart button** on every stage — cascades downstream resets
- **Artifact viewer**: JSON output with syntax highlighting (`vscDarkPlus`, `#000b21` background)
- **MANIFEST stage** renders as a summary dashboard (entity + chunk count cards), not raw JSON

---

## 10. Infrastructure & DevOps

### Service Dependencies

| Service | Purpose | Hosting |
|---|---|---|
| PostgreSQL | Relational store | Local / Supabase |
| AWS S3 (or compatible) | Artifact object storage | AWS / MinIO |
| Redis | Celery broker + result backend + semantic cache | Local / Redis Cloud |
| Qdrant | Vector store | Qdrant Cloud |
| Neo4j | Knowledge graph | Neo4j AuraDB |
| Infinity Server | GPU embedding + reranking | Local CUDA machine |
| Celery Worker | Async pipeline execution | Local / Docker |

### LLM Provider Flexibility (`LLMFactory`)

| Provider | LLM | Embedding |
|---|---|---|
| `gemini` | gemini-3.5-flash-lite | gemini-embedding-2 |
| `openai` | gpt-4o-mini | text-embedding-3-small |
| `anthropic` | claude-3-5-sonnet | — |
| `groq` | llama-3.3-70b-versatile | — |
| `huggingface` | endpoint models | all-MiniLM-L6-v2 |
| `infinity` | — | BAAI/bge-small-en-v1.5 (GPU) |
| `local` | — | HuggingFace local load |

**BYOK**: Per-request LLM credentials supported — institutions can use their own API keys without them being stored server-side.

**Migrations**: Managed via Alembic. `create_all()` is disabled in production.

---

## 11. Security Architecture

| Layer | Mechanism |
|---|---|
| Authentication | JWT HS256 — 30-min access + 7-day refresh tokens |
| Authorization | RBAC: `ADMIN` / `PUBLISHER` / `STUDENT` |
| Route Guards | `require_role([...])` FastAPI dependency per router |
| Security Headers | CSP, HSTS, X-Frame-Options via `SecurityHeadersMiddleware` |
| Audit Logging | Full request/response logging via `RequestLoggerMiddleware` |
| Error Handling | Centralized handlers — no stack traces exposed to clients |
| Soft Deletes | `is_deleted` + `deletion_status` on all core entities |

---

## 12. Key Design Decisions

| Decision | Rationale |
|---|---|
| Docling as primary parser | GPU layout analysis handles multi-column academic PDFs and tables far better than text extractors |
| LlamaParse as fallback | Guarantees 100% parse coverage even for Docling edge cases |
| GLiNER over spaCy NER | Zero-shot NER with custom academic labels — no fine-tuning required |
| ENTITY before CHUNK | Chunker uses entity IDs as metadata anchors; without entities first, concept-filtered retrieval is impossible |
| RRF for result fusion | Backend scores are incomparable in scale; RRF uses only rank position, requiring no calibration |
| Dedicated GPU embedding server | 30x latency reduction vs. CPU; OpenAI-compatible API makes it a transparent drop-in |
| Celery over threading | True background worker process; restartable independently; task status persisted in Redis |
| Idempotent retries | Every stage deletes its own prior output before re-writing; Qdrant vectors purged before re-indexing |

---

## 13. Current Status

| Area | Status |
|---|---|
| PARSE → MANIFEST pipeline (automated) | ✅ Complete |
| Entity extraction (GLiNER + LLM hybrid) | ✅ Working |
| Relation extraction (structural + spaCy) | ✅ Working |
| Semantic chunking (entity-aware) | ✅ Working |
| Vector indexing (Qdrant) | ✅ Working |
| Hybrid RAG chat | ✅ Working |
| Neo4j graph write | ⚠️ Placeholder — retrieval reads graph but full population in progress |
| Analysis Studio (all types) | ✅ Working (manually triggered) |
| Cross-document analysis | ✅ Working |
| MCP server | ✅ Mounted, tools defined |
| Semantic cache | ✅ Implemented |
| BYOK per-request LLM | ✅ Implemented |
| Document versioning + old-vector cleanup | ✅ Working |
| Soft deletes everywhere | ✅ Complete |
| Alembic migrations | ✅ Active |

---

## 14. End-to-End Data Flow

```
User uploads PDF
        │
        ▼ POST /api/v1/documents
   S3: original file stored
   PostgreSQL: Document row created (status=PENDING)
        │
        ▼ Celery task chain auto-triggered
[PARSE]   Docling (GPU) ─────────────────────────── S3: canonical.json
           ↳ fallback: LlamaParse                        document.md
                                                         pages/NNN.png
        │
        ▼
[AST]   Docling path: no-op
        LlamaParse path: ASTBuilder → ──────────── S3: canonical.json
        │
        ▼
[ENTITY]  GLiNER NER + LLM extraction ──────────── S3: entities.json
        │
        ▼
[RELATION] AST structural rules + spaCy ─────────── S3: relations.json
        │
        ▼
[GRAPH]   Neo4j entity/relation upsert ──────────── Neo4j AuraDB
        │
        ▼
[CHUNK]   ASTChunker (entity-aware, 500-tok) ────── S3: chunks.json
        │
        ▼
[EMBED]   Infinity GPU embed → Qdrant upsert ─────── Qdrant Cloud
           ↳ old vectors purged first
        │
        ▼
[MANIFEST] LLM summary → ───────────────────────── S3: summary.md
           manifest stats                               manifest.json
           PostgreSQL: status=COMPLETED

━━━━━━━━━━━ Document is now fully ready ━━━━━━━━━━━

Student query → Chat UI
    │
    ▼ Query Planner (intent classification)
    ▼ asyncio.gather(Qdrant, Neo4j, PostgreSQL)
    ▼ Reciprocal Rank Fusion
    ▼ Cross-Encoder Rerank (Infinity GPU)
    ▼ LLM Answer Generation with [CIT-N] citations
    ▼ Response returned to student
```
