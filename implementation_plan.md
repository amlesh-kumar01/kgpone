# KnowledgeOS — Refined 10-Phase Architecture Plan

## Core Principle

> Parse once. Understand once. Enrich once.
> Every downstream feature (summary, quiz, comparison, formula revision)
> reuses the same knowledge package — never re-parses the PDF.

---

## Three-Layer Contract (Non-Negotiable Rules)

```
┌─────────────────────────────────────────────────────────┐
│  S3 = Artifact Store                                    │
│  • Original PDF, page images, figures                   │
│  • Parser outputs (Docling JSON, LlamaParse JSON)       │
│  • Canonical AST JSON, Hierarchy JSON                   │
│  • Entities, Concepts, Relations, Formulas, Questions   │
│  • Chunks JSON                                          │
│  • Summaries, Quizzes, Comparisons (JSON + Markdown)    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  PostgreSQL = Control + Index Layer                     │
│  • Document metadata (title, type, course, status)      │
│  • S3 object keys (never signed URLs)                   │
│  • Processing state (ingestion_jobs per stage)          │
│  • Analysis job metadata (analysis_jobs)                │
│  • Lightweight entity/formula/question indexes          │
│  • Course relationships, permissions, versions          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Canonical JSON = Source of Truth for Document Structure│
│  • canonical.json is the authoritative AST              │
│  • Qdrant/Neo4j are derived indexes, not sources        │
│  • If Qdrant is wiped, rebuild from canonical.json      │
│  • If Neo4j is wiped, rebuild from relations.json       │
└─────────────────────────────────────────────────────────┘
```

**PostgreSQL does NOT store large JSON artifacts.**
**Signed URLs are generated on-demand, never stored.**
**The canonical JSON is never derived from Qdrant or Neo4j.**

---

## Provenance Chain (Must be traceable end-to-end)

```
Generated Question
       ↓ concept_ids
Canonical Concept
       ↓ source_node_ids
AST Node (ASTNode.id)
       ↓ section_id
Section (canonical.json)
       ↓ source.page_start
Page number
       ↓ document_id
Original PDF (s3_key)
```

Every artifact — entity, formula, question, summary, quiz question — must be
traceable to the source page in the source PDF.

---

## S3 Ownership Model

```
                      KnowledgeOS S3 Bucket
                               │
              ┌────────────────┴──────────────────┐
              │                                    │
        documents/                           analyses/
              │                                    │
   {dept}/{course}/{offering}/             {analysis_id}/
              │                                    │
          {doc_id}/                         manifest.json
              │                             input.json
    ┌─────────┼──────────┐                  result.json
    │         │          │                  result.md
  PDF       AST       Knowledge
```

**Rule:** `documents/{dept}/{course}/{offering}/{doc_id}/` owns **everything**
belonging to that document. Nothing document-specific lives outside this prefix.

**Rule:** `analyses/{analysis_id}/` owns everything for **multi-document**
or **user-selected** analyses. These are never nested under a single document.

---

## S3 Tree

```
s3://bucket/
  documents/
    {dept}/
      {course_code}/
        {year}_{semester}/
          {doc_id}/
            original/
              document.pdf          ← uploaded file (replaces scattered key)

            pages/
              001.png               ← per-page renders (Phase 2)
              002.png

            assets/
              figure_001.png        ← extracted figures
              table_001.png         ← extracted table images
              eq_001.png            ← equation renders (optional)

            parsers/
              docling.json          ← raw Docling structured output
              llamaparse.json       ← raw LlamaParse output (only when triggered)

            canonical/
              canonical.json        ← CanonicalDocument AST (source of truth)
              hierarchy.json        ← hierarchy confidence report

            knowledge/
              entities.json         ← typed entities with provenance
              concepts.json         ← resolved canonical concepts
              relations.json        ← relationships with confidence + method
              formulas.json         ← formulas with LaTeX + variables
              questions.json        ← extracted/classified questions

            retrieval/
              chunks.json           ← all chunks with rich metadata

            analysis/
              summary/
                {analysis_id}.json
                {analysis_id}.md
              quizzes/
                {analysis_id}.json
                {analysis_id}.md
              formula_revision/
                {analysis_id}.json
                {analysis_id}.md
              pyq_mapping/
                {analysis_id}.json

            manifest.json           ← master artifact index (at root of doc prefix)
            ingestion_log.json      ← per-stage status, timing, errors

  analyses/
    {analysis_id}/                  ← multi-document / course-level analyses
      manifest.json
      input.json
      result.json
      result.md
```

> **Why `{dept}/{course}/{offering}/{doc_id}/`?**
> It preserves the existing organizational hierarchy (already used for the
> old file key), while adding `{doc_id}/` as the unified namespace root.
> The `{doc_id}/` folder boundary is the important invariant — everything
> inside belongs to exactly one document.

---

## PostgreSQL Entity Map

```
documents
  ├── id (PK)                       ← document_id
  ├── s3_prefix                  ← NEW: full prefix up to doc_id/
  │                                     "documents/{dept}/{course}/{offering}/{doc_id}"
  ├── original_s3_key            ← NEW: "…/{doc_id}/original/document.pdf"
  ├── manifest_s3_key            ← NEW: "…/{doc_id}/manifest.json"
  ├── parser_used                ← NEW: "docling" | "llamaparse"
  ├── parser_version             ← NEW
  ├── quality_score              ← NEW: 0.0–1.0
  ├── processing_version         ← NEW: "2.0"
  ├── [all existing columns unchanged]
  └── s3_key (existing)          ← deprecated but kept for old records

ingestion_jobs                   ← NEW
  ├── id (PK)
  ├── document_id (FK → documents)
  ├── stage        ← PARSE|QUALITY|AST|FORMULA|QUESTION|ENTITY|RELATION|CHUNK|EMBED|GRAPH|MANIFEST
  ├── status       ← PENDING|RUNNING|COMPLETED|FAILED|SKIPPED
  ├── input_s3_key               ← S3 key of stage input artifact
  ├── output_s3_key              ← S3 key of stage output artifact
  ├── model_version              ← "docling-2.0", "gliner-medium-v2.1"
  ├── error_message
  ├── started_at
  └── completed_at

analysis_jobs                    ← NEW
  ├── id (PK)                    ← analysis_id
  ├── analysis_type              ← "summarize"|"quiz"|"compare"|"formula_revision"|"pyq_mapping"
  ├── status
  ├── source_document_ids        ← JSON array
  ├── source_node_ids            ← JSON array
  ├── source_concept_ids         ← JSON array
  ├── options                    ← JSONB
  ├── result_s3_key
  ├── result_md_s3_key
  ├── model_version
  ├── prompt_version
  ├── created_at
  └── completed_at

extracted_entities               ← NEW (lightweight index, full data in S3)
  ├── id, document_id (FK), canonical_name, entity_type, confidence, source_page

extracted_formulas               ← NEW
  ├── id, document_id (FK), latex, equation_label, source_page

extracted_questions              ← NEW
  ├── id, document_id (FK), question_type, marks, year, exam, source_page

cleanup_jobs                     ← existing (unchanged, but cleanup logic updated)
```

---

## Deletion Lifecycle

```
DELETE /documents/{document_id}
         │
         ▼
1. Soft-delete: is_deleted=True, deletion_status=PENDING
2. Create CleanupJob
3. Dispatch cleanup_document_task.delay()
         │
         ▼  (idempotent — safe to retry any step)
4. Cancel RUNNING ingestion_jobs for this document
5. s3.list_and_delete_prefix(f"{doc.s3_prefix}/")   ← ONE call, deletes everything
6. Qdrant: delete_by_filter({document_id: doc_id})
7. Neo4j: delete_document_entities(doc_id)
8. PostgreSQL: delete extracted_entities, extracted_formulas, extracted_questions
9. PostgreSQL: delete ingestion_jobs
10. Hard-delete Document record
11. CleanupJob → COMPLETED
```

---

## Service Layout (Target)

```
src/
  services/
    ingestion/
      artifact_manager.py         ← NEW (Phase 1 foundation)
      pipeline.py                 ← MODIFY (staged v2 + keep old as fallback)
      metadata_builder.py         ← existing (minor extension)

      parser/
        base.py                   ← MODIFY: return CanonicalDocument
        docling_parser.py         ← NEW
        llama_parser.py           ← MODIFY: add to_canonical() adapter

      quality/
        quality_evaluator.py      ← NEW

      canonical/
        ast_schema.py             ← NEW Pydantic models
        ast_builder.py            ← NEW

      hierarchy/
        hierarchy_engine.py       ← NEW

      extraction/
        base.py                   ← existing
        gliner_extractor.py       ← MODIFY: 30 labels + provenance
        entity_resolver.py        ← MODIFY: provenance-aware
        formula_extractor.py      ← NEW
        question_extractor.py     ← NEW
        relation_extractor.py     ← NEW (replaces spacy_relation_extractor.py)
        llm_extractor.py          ← existing (LLM fallback, untouched)

      chunking/
        base.py                   ← existing
        dom_chunker.py            ← existing (fallback)
        ast_chunker.py            ← NEW

      embedding/
        base.py                   ← existing
        llm_embedding.py          ← existing (untouched)

      upload_manager/
        document_service.py       ← MODIFY: new S3 prefix convention

    analysis/                     ← NEW
      base.py                     ← AnalysisInput / AnalysisResult / BaseAnalysisJob
      summarization/
        document_summarizer.py
        section_summarizer.py
        course_summarizer.py
      quiz/
        quiz_generator.py
      formula_revision/
        formula_revision.py
      pyq_mapping/
        pyq_mapper.py
      comparison/
        document_comparator.py

    retrieval/                    ← NEW (Phase 5 — before analysis)
      unified_retriever.py
      qdrant_retriever.py
      neo4j_retriever.py

    inspection/                   ← NEW (Phase 4 — early)
      document_inspector.py

  repositories/
    s3/
      storage_repository.py       ← MODIFY: upload_json, upload_text, download_json, exists
    qdrant/
      vector_repository.py        ← MODIFY: richer payload indexes
    neo4j/
      graph_repository.py         ← MODIFY: Section/Formula/Question nodes

  models/
    document_model.py             ← MODIFY
    ingestion_job_model.py        ← NEW
    analysis_job_model.py         ← NEW
    extracted_entity_model.py     ← NEW
    extracted_formula_model.py    ← NEW
    extracted_question_model.py   ← NEW
    system_model.py               ← existing

  workers/tasks/
    ingestion_tasks.py            ← MODIFY: decompose into per-stage tasks
    analysis_tasks.py             ← NEW
    cleanup_tasks.py              ← MODIFY: single-prefix deletion

  api/routes/
    document_routes.py            ← MODIFY
    analysis_routes.py            ← NEW
    inspection_routes.py          ← NEW
```

---

---

# PHASE 1 — S3 Namespace + ArtifactManager + Manifest
**"Build the document's S3 home. Everything else is built on this."**

### Goal

Every document gets an isolated S3 prefix. Every artifact generated from
that document lives under that prefix. Deletion is a single S3 prefix wipe.

### Files changed

#### [NEW] `src/services/ingestion/artifact_manager.py`

```python
class ArtifactManager:
    """
    Single source of truth for all S3 key conventions for one document.
    Injected into every pipeline stage. Never hard-code S3 paths elsewhere.
    """
    def __init__(self, document_id: str, s3_prefix: str, s3: S3Storage): ...

    # Key conventions — all derived from s3_prefix
    def original_key(self, filename: str) -> str
    def parser_key(self, parser_name: str) -> str  # parsers/docling.json
    def canonical_key(self) -> str                 # canonical/canonical.json
    def hierarchy_key(self) -> str                 # canonical/hierarchy.json
    def knowledge_key(self, artifact: str) -> str  # knowledge/{artifact}.json
    def chunks_key(self) -> str                    # retrieval/chunks.json
    def asset_key(self, filename: str) -> str      # assets/{filename}
    def page_key(self, page_num: int) -> str       # pages/001.png
    def analysis_key(self, type: str, analysis_id: str, ext: str) -> str
    def manifest_key(self) -> str                  # manifest.json
    def log_key(self) -> str                       # ingestion_log.json

    # S3 helpers — no raw boto3 calls outside this class
    def upload_json(self, key: str, data: dict) -> str
    def upload_text(self, key: str, text: str) -> str
    def download_json(self, key: str) -> dict
    def exists(self, key: str) -> bool
    def prefix(self) -> str                        # full prefix for deletion

    # Manifest management
    def read_manifest(self) -> dict
    def update_manifest(self, updates: dict) -> None
    def init_manifest(self, doc_metadata: dict) -> None
```

#### [MODIFY] `src/models/document_model.py`

Add nullable columns (backward compatible — existing records get `None`):
```python
s3_prefix: str | None        # "documents/CS/CS101/2025_ODD/{doc_id}"
original_s3_key: str | None  # "…/original/document.pdf"
manifest_s3_key: str | None  # "…/manifest.json"
parser_used: str | None
parser_version: str | None
quality_score: float | None
processing_version: str | None
```

#### [NEW] `src/models/ingestion_job_model.py`

```python
class IngestionStage(str, Enum):
    PARSE = "PARSE"
    QUALITY = "QUALITY"
    AST = "AST"
    FORMULA = "FORMULA"
    QUESTION = "QUESTION"
    ENTITY = "ENTITY"
    RELATION = "RELATION"
    CHUNK = "CHUNK"
    EMBED = "EMBED"
    GRAPH = "GRAPH"
    MANIFEST = "MANIFEST"

class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"
    id, document_id (FK), stage, status,
    input_s3_key, output_s3_key,
    model_version, error_message,
    started_at, completed_at
```

#### [MODIFY] `src/services/ingestion/upload_manager/document_service.py`

`generate_upload_url()` flow changes:
1. Create `Document` record **first** (get `doc_id`)
2. Compute `s3_prefix = documents/{dept}/{course}/{offering}/{doc_id}`
3. `original_s3_key = s3_prefix/original/{filename}`
4. Generate presigned URL for `original_s3_key`
5. Store `s3_prefix` + `original_s3_key` in DB
6. Return presigned URL + `document_id`

Old: `documents/{dept}/{course}/{offering}/{uuid}_file.pdf` (no doc_id folder)
New: `documents/{dept}/{course}/{offering}/{doc_id}/original/document.pdf`

#### [MODIFY] `src/repositories/s3/storage_repository.py`

Add:
```python
def upload_json(self, key: str, data: dict) -> str
def upload_text(self, key: str, text: str) -> str
def download_json(self, key: str) -> dict
def exists(self, key: str) -> bool
```

#### [MODIFY] `src/workers/tasks/cleanup_tasks.py`

```python
# Step 5 — replaces two separate calls
s3.list_and_delete_prefix(doc.s3_prefix + "/")
```

### Acceptance Criteria

- ✅ Upload PDF → `documents/{dept}/{course}/{offering}/{doc_id}/original/document.pdf`
- ✅ `manifest.json` created at `…/{doc_id}/manifest.json` and readable via API
- ✅ Delete document → entire prefix wiped in one S3 call
- ✅ Old documents (with legacy `s3_key`) still delete correctly
- ✅ Existing ingestion flow still works end-to-end (no regressions)
- ✅ Alembic migration runs cleanly

---

# PHASE 2 — Canonical AST + DoclingParser + Quality Routing
**"Replace LlamaParse as primary. Make parsing output a persisted, inspectable artifact."**

### Goal
Document parsing produces a typed, provenance-rich `CanonicalDocument` AST
that is saved to S3 and becomes the input for all downstream stages.

### Step-by-Step Implementation Plan

#### Step 2A: Dependency and Schema Update
**Objective:** Add `docling` dependency and create the `ast_schema.py` models.
1. Modify `pyproject.toml` to add `docling>=2.0.0`. Run `uv sync` or install dependencies.
2. Create `src/services/ingestion/canonical/ast_schema.py`.
3. Define `NodeType` (Enum).
4. Define `NodeSource`, `ASTNode`, `ParserProvenance`, and `CanonicalDocument` Pydantic models.
5. Note: Ensure `source.bbox` and other provenance fields are correctly typed. Keep old `dom_schema.py` intact for backward compatibility.

#### Step 2B: DoclingParser Implementation
**Objective:** Implement the new Docling parser.
1. Modify `src/infrastructure/model_factory.py` to add a singleton `get_docling()` (or equivalent initialization for Docling models if needed).
2. Create `src/services/ingestion/parser/docling_parser.py`.
3. Implement `DoclingParser` which parses PDF, maps `DoclingDocument` to `CanonicalDocument` nodes.
4. Save raw Docling output to `…/parsers/docling.json` (using ArtifactManager).
5. Extract page images and embedded figures and save them to `…/pages/` and `…/assets/`.

#### Step 2C: LlamaParse Adapter
**Objective:** Keep LlamaParse as a fallback by adding an adapter.
1. Modify `src/services/ingestion/parser/llama_parser.py`.
2. Add a `to_canonical(dom: DocumentDOM) -> CanonicalDocument` adapter function.
3. Keep the existing LlamaParse logic unchanged, just map the output.

#### Step 2D: Quality Evaluator
**Objective:** Build the logic to score parsing quality and route between parsers.
1. Create `src/services/ingestion/quality/quality_evaluator.py`.
2. Implement scoring logic based on text density, heading detection, garbled text, table extraction, etc.
3. Return `QualityReport(score, needs_fallback, fallback_reason)`.

#### Step 2E: AST Builder & Hierarchy Engine
**Objective:** Select the winner, build the final AST, and reconstruct hierarchy.
1. Create `src/services/ingestion/canonical/ast_builder.py`.
2. Implement logic: Try Docling -> Evaluate Quality -> If score < 0.5 or 0.75, try LlamaParse -> Pick winner -> Build `CanonicalDocument`.
3. Create `src/services/ingestion/hierarchy/hierarchy_engine.py`.
4. Implement multi-signal hierarchy reconstruction (section numbers, fonts, etc.).
5. Save `canonical.json` and `hierarchy.json` via ArtifactManager.

#### Step 2F: Pipeline Integration
**Objective:** Wire Phase 2 into `pipeline.py` and `ingestion_tasks.py`.
1. Modify `pipeline.py` to use `ast_builder` instead of just `parser.parse()`.
2. Ensure the `quality_score` is updated on the `Document` database record.
3. Ensure `manifest.json` is updated with `parsers` + `canonical` keys.

### Acceptance Criteria
- ✅ `…/parsers/docling.json` is valid JSON with Docling native output
- ✅ `…/canonical/canonical.json` has typed AST nodes with `source.bbox`
- ✅ `documents.quality_score` updated after parsing
- ✅ If Docling score < 0.5 → `…/parsers/llamaparse.json` also exists
- ✅ `manifest.json` updated with `parsers` + `canonical` artifact keys

---

# PHASE 3 — Knowledge Extraction
**"Build the knowledge package from the canonical AST."**

### Goal
Extract entities, formulas, questions, and relationships from the canonical AST.
Save as structured JSON artifacts. Insert lightweight indexes into PostgreSQL.

### Step-by-Step Implementation Plan

#### Step 3A: Database Models for Extractions
**Objective:** Create lightweight index rows in PostgreSQL pointing to S3 artifacts.
1. Modify `src/models/academic_model.py` (or create a new model file like `knowledge_model.py`) to add `ExtractedEntity`, `ExtractedFormula`, `ExtractedQuestion` tables.
2. Link them to `Document` via `document_id`.
3. Generate and run Alembic migrations.

#### Step 3B: Entity Extraction & Resolution
**Objective:** Upgrade GLiNER and EntityResolver to use Canonical AST.
1. Modify `src/services/ingestion/extraction/gliner_extractor.py`.
2. Change input from raw text to `List[ASTNode]`.
3. Preserve `source_node_id` and `source_page` in output.
4. Modify `src/services/ingestion/extraction/entity_resolver.py` to aggregate `surface_forms` and `source_node_ids`.
5. Save extracted entities to `…/knowledge/entities.json`.

#### Step 3C: Formula Extraction
**Objective:** Extract standalone and inline equations.
1. Create `src/services/ingestion/extraction/formula_extractor.py`.
2. Extract all `EQUATION`/`FORMULA` AST nodes natively from Docling.
3. Parse inline LaTeX (e.g. `$E=mc^2$`) from `PARAGRAPH` nodes using regex.
4. Attempt variable extraction from surrounding 200-char context.
5. Save to `…/knowledge/formulas.json`.

#### Step 3D: Question Extraction
**Objective:** Extract practice questions and past year questions (PYQs).
1. Create `src/services/ingestion/extraction/question_extractor.py`.
2. Extract all `QUESTION` AST nodes from Docling.
3. Use regex (numbered lists, `?`, MCQ patterns A/B/C/D) on paragraphs.
4. Inject PYQ metadata from document context (year, exam).
5. Save to `…/knowledge/questions.json`.

#### Step 3E: Relation Extraction
**Objective:** Extract relationships between entities/concepts.
1. Create `src/services/ingestion/extraction/relation_extractor.py` (replacing/upgrading `spacy_relation_extractor.py`).
2. Use structural rules (high confidence) from AST hierarchy (e.g., Section Header -> Concepts in body).
3. Use spaCy dependency parsing (medium confidence) for sentence-level relations.
4. Save to `…/knowledge/relations.json`.

#### Step 3F: Neo4j Graph Builder Integration
**Objective:** Push the new ontology into the knowledge graph.
1. Modify `src/repositories/neo4j/graph_repository.py`.
2. Add methods to upsert `:Section`, `:Formula`, `:Question` nodes.
3. Add methods for new relationships: `(Document)-[:CONTAINS]->(Section)`, `(Section)-[:EXPLAINS]->(Concept)`, `(Concept)-[:HAS_FORMULA]->(Formula)`, `(Question)-[:TESTS]->(Concept)`.

### Acceptance Criteria
- ✅ `…/knowledge/entities.json` — typed entities with source_page
- ✅ `…/knowledge/formulas.json` — formulas with LaTeX + variables
- ✅ `…/knowledge/questions.json` — classified questions with source_page
- ✅ `…/knowledge/relations.json` — relations with confidence + method
- ✅ Neo4j has Section/Formula/Question nodes linked to Document

---

# PHASE 4 — Inspection Layer
**"Make every artifact visible before building analysis on top."**

> Inspection is prioritized early because you cannot trust what you cannot see.
> Getting this right before building analysis features saves enormous debugging time.

### Goal
A developer or admin can open any document and see every artifact — canonical AST, entities, formulas, questions, chunks — linked back to source pages.

### Step-by-Step Implementation Plan

#### Step 4A: Core Inspector Service
**Objective:** Build `DocumentInspector` to aggregate all S3/Postgres/Qdrant/Neo4j data.
1. Create `src/services/inspection/document_inspector.py`.
2. Define `InspectionReport` Pydantic model (with canonical/knowledge/qdrant/neo4j summaries).
3. Implement `inspect(document_id)` which:
   - Uses `ArtifactManager` to check if keys exist in S3.
   - Queries `documents` and `ingestion_jobs` tables.
   - Queries Neo4j for node/relationship counts.

#### Step 4B: Inspection API Routes
**Objective:** Expose the inspection functionality via FastAPI.
1. Create `src/api/routes/inspection_routes.py`.
2. Implement endpoints:
   - `GET /api/v1/inspect/{doc_id}` (full report)
   - `GET /api/v1/inspect/{doc_id}/manifest`
   - `GET /api/v1/inspect/{doc_id}/canonical`
   - `GET /api/v1/inspect/{doc_id}/knowledge/{type}` (entities, formulas, questions, relations)
   - `GET /api/v1/inspect/{doc_id}/stages`
3. Wire the router into `src/api/main.py`.

#### Step 4C: Vanilla JS Debug Dashboard
**Objective:** Build a simple frontend to visualize the pipeline.
1. Create a `debug/` folder in the project root.
2. Build an `index.html` (vanilla JS + Tailwind via CDN or plain CSS).
3. Fetch list of documents -> click to view `InspectionReport` -> browse artifacts.
4. (Optional) Run a simple Python HTTP server to serve the page, or serve via FastAPI static files.

### Acceptance Criteria

- ✅ `GET /inspect/{doc_id}` returns full report in < 2 seconds
- ✅ Every artifact key in the report is either `exists: true` or `exists: false`
- ✅ `/debug` page renders document list and artifact tree
- ✅ A broken ingestion (failed stage) is visible with error message

---

# PHASE 5 — AST-Aware Chunking + Staged Celery Pipeline
**"Rich retrieval chunks. Each ingestion stage independently retryable."**

### Goal
Chunks carry full knowledge context (heading path, concept IDs, formula IDs).
The monolithic Celery task is decomposed into per-stage tasks that read/write S3 artifacts and track state in `ingestion_jobs`.

### Step-by-Step Implementation Plan

#### Step 5A: AST Chunker
**Objective:** Create a chunking strategy that respects hierarchy and injects metadata.
1. Create `src/services/ingestion/chunking/ast_chunker.py`.
2. Traverse the `CanonicalDocument` tree. Keep `EQUATION`, `TABLE`, and `IMAGE` as separate chunks. Group `PARAGRAPH` and `LIST` into larger text chunks based on token limits.
3. For each chunk, compute the `heading_path` (by walking up the parent tree to `SECTION` nodes).
4. Inject `concept_ids` and `formula_ids` by cross-referencing node IDs with extracted knowledge in `entities.json` and `formulas.json`.
5. Save outputs to `…/retrieval/chunks.json`.

#### Step 5B: Qdrant Indexing Updates
**Objective:** Store chunks with rich payloads.
1. Modify `src/repositories/qdrant/vector_repository.py`.
2. Ensure the payload schemas support `section_id` (keyword), `heading_path` (text), `concept_ids` (keyword[]), `formula_ids` (keyword[]).
3. Ensure backwards compatibility with existing simple text payloads if necessary.

#### Step 5C: Celery Task Decomposition
**Objective:** Refactor the pipeline into chained background tasks.
1. Modify `src/workers/tasks/ingestion_tasks.py`.
2. Remove `process_document_task`.
3. Create individual tasks:
   - `parse_document_task`
   - `build_canonical_ast_task`
   - `extract_formulas_task`
   - `extract_questions_task`
   - `extract_entities_task`
   - `extract_relations_task`
   - `build_chunks_task`
   - `index_qdrant_task`
   - `build_neo4j_task`
   - `finalize_manifest_task`
4. Each task reads its state from `ingestion_jobs` (set to RUNNING), reads the S3 input artifact, executes the code, uploads the S3 output artifact, and updates `ingestion_jobs` to COMPLETED, then dispatches the next task using Celery `chain` or direct `.delay()`.

#### Step 5D: Stage Retry API
**Objective:** Allow restarting ingestion from a specific failed stage.
1. Modify `src/api/routes/document_routes.py`.
2. Add `POST /documents/{doc_id}/retry-stage`.
3. Logic: Mark the failed `ingestion_job` as PENDING and `.delay()` its specific task.

### Acceptance Criteria
- ✅ Uploading a document creates 10+ sequential `ingestion_jobs` rows.
- ✅ `chunks.json` artifacts have `heading_path` arrays.
- ✅ Qdrant points have rich metadata.
- ✅ API allows retrying an isolated stage without re-triggering Docling parsing.

---

# PHASE 6 — Analysis Framework + Document Summarization
**"Consume the knowledge package. Never re-parse the PDF."**

### Goal
    provenance: AnalysisProvenance

class BaseAnalysisJob(ABC):
    @abstractmethod
    async def run(self, input: AnalysisInput, analysis_id: str) -> AnalysisResult: ...
```

#### [NEW] `src/services/analysis/summarization/document_summarizer.py`

1. Load `canonical.json` → chapter/section hierarchy
2. Load `knowledge/entities.json` → key concepts
3. Load `retrieval/chunks.json` → source text per section
4. Hierarchical LLM calls: section → chapter → document
5. Every summary section has `source_nodes: [node_id, …]`
6. Save `…/analysis/summary/{analysis_id}.json` + `.md`

#### [NEW] `src/models/analysis_job_model.py`

#### [NEW] `src/workers/tasks/analysis_tasks.py`

```python
@shared_task
def summarize_document_task(document_id, analysis_id, options): ...
```

#### [NEW] `src/api/routes/analysis_routes.py`

```
POST /analysis/summarize       → creates analysis_job, returns analysis_id
GET  /analysis/{analysis_id}   → status + metadata
GET  /analysis/{analysis_id}/download  → presigned URL for JSON + MD
```

### Acceptance Criteria

- ✅ `POST /analysis/summarize` → Celery task runs → JSON + MD saved to S3
- ✅ Summary JSON has `source_nodes` on every section
- ✅ **PDF is never loaded during analysis** (all reads from S3 JSON artifacts)
- ✅ Running the same summarize request twice creates two different `analysis_id` entries

---

# PHASE 7 — Retrieval Layer
**"Analysis pipelines never query Qdrant or Neo4j directly."**

### Goal
All analysis services go through a `UnifiedRetriever`. This decouples analysis logic from storage implementation and makes it easier to add hybrid retrieval, reranking, or graph expansion later.

### Step-by-Step Implementation Plan

#### Step 7A: Retrieval Models and Service Stub
**Objective:** Define schemas for retrieval results.
1. Create `src/services/retrieval/unified_retriever.py`.
2. Define `RetrievalResult`, `SourceRef`, and `UnifiedRetriever` class stub.

#### Step 7B: Qdrant and Neo4j Integration
**Objective:** Implement the retrieval logic.
1. Implement `retrieve()` to:
   - Perform semantic search via `QdrantRepository.search()`.
   - Query `Neo4jRepository` for related graph concepts (prerequisites).
   - Merge Qdrant text chunks with Neo4j context.

#### Step 7C: Refactor RAG Chat
**Objective:** Replace direct Qdrant calls in RAG endpoints with `UnifiedRetriever`.
1. Modify `src/services/rag/retrieval/qdrant_retriever.py` or the Chat service (`answer_service.py`) to use `UnifiedRetriever` instead of calling Qdrant and Neo4j separately.
2. Ensure source citations correctly map back to the unified provenance.

### Acceptance Criteria
- ✅ RAG chat works through `UnifiedRetriever`.
- ✅ Analysis services use `UnifiedRetriever` (no direct Qdrant calls).
- ✅ Graph context (prerequisites, related concepts) is appended to retrieval results.

---

# PHASE 8 — Educational Analysis (Quiz, Formula Revision, PYQ Mapping)
**"Build the educational intelligence layer."**

### Goal
Implement specialized educational analysis tools that utilize the extracted artifacts (questions, formulas, entities) to produce study materials.

### Step-by-Step Implementation Plan

#### Step 8A: Quiz Generator Service
**Objective:** Automatically generate a study quiz.
1. Create `src/services/analysis/quiz/quiz_generator.py` implementing `BaseAnalysisJob`.
2. Logic:
   - Load `questions.json` (extracted during ingestion) for seeded questions.
   - Use `litellm` to augment/reformat them into a structured quiz format.
   - Ensure every question retains `sources` mapped to the original AST node/chunk.
3. Save output to `analysis/quiz/{analysis_id}.json` & `.md`.

#### Step 8B: Formula Revision Sheet Service
**Objective:** Generate a formula sheet with definitions and related concepts.
1. Create `src/services/analysis/formula_revision/formula_revision.py` implementing `BaseAnalysisJob`.
2. Logic:
   - Load `formulas.json`.
   - Query Neo4j (via `UnifiedRetriever` graph context or directly via Graph Repo) for related concepts for each formula.
   - Format into a revision sheet.
3. Save output to `analysis/formula_revision/{analysis_id}.json` & `.md`.

#### Step 8C: API Endpoints & Tasks
**Objective:** Expose the services to the frontend.
1. Add `generate_quiz_task` and `generate_formula_revision_task` to `src/workers/tasks/analysis_tasks.py`.
2. Add `POST /api/v1/analysis/quiz` and `POST /api/v1/analysis/formula-revision` to `src/api/routes/analysis_routes.py`.

### Acceptance Criteria
- ✅ Quiz service returns JSON where every question has `sources: [{document_id, node_id, page}]`.
- ✅ Formula revision service returns formulas with extracted variables and related concept connections.
- ✅ New endpoints correctly queue the celery tasks and return the analysis IDs.

---

# PHASE 9 — Multi-Document Analysis + Comparison
**"Course-level intelligence. No PDF merging."**

### Goal
Perform analysis across multiple documents simultaneously. Instead of merging PDFs, the services will iterate over the individual JSON artifacts of each document in S3 and aggregate the insights.

### Step-by-Step Implementation Plan

#### Step 9A: Course Summarizer Service
**Objective:** Aggregate summaries across multiple documents.
1. Create `src/services/analysis/summarization/course_summarizer.py` implementing `BaseAnalysisJob`.
2. Logic:
   - Load `canonical.json` or `chunks.json` from multiple documents simultaneously.
   - Use `litellm` (map-reduce style) to aggregate and synthesize a holistic course summary.
   - Track provenance by mapping final summary sections to source document IDs.
3. Save to `analysis/course_summary/{analysis_id}.json` & `.md`.

#### Step 9B: Document Comparator Service
**Objective:** Compare concepts and formulas between two or more documents.
1. Create `src/services/analysis/comparison/document_comparator.py` implementing `BaseAnalysisJob`.
2. Logic:
   - Load `entities.json` and `formulas.json` from multiple documents.
   - Find intersection (common concepts) and symmetric differences (unique to Document A, unique to Document B).
   - Format a comprehensive diff report.
3. Save to `analysis/comparison/{analysis_id}.json` & `.md`.

#### Step 9C: API Endpoints & Tasks
**Objective:** Wire the multi-document analysis tools to the API.
1. Add `course_summary_task` and `document_comparison_task` to `src/workers/tasks/analysis_tasks.py`.
2. Add `POST /api/v1/analysis/course-summary` and `POST /api/v1/analysis/compare` to `src/api/routes/analysis_routes.py`, both accepting arrays of `document_ids`.

### Acceptance Criteria
- ✅ `POST /analysis/compare` with `documents: [A, B]` successfully returns an `analysis_id`.
- ✅ Comparison lists: concepts in A not in B, common concepts, formula differences.
- ✅ Multi-doc results correctly handle provenance for each separate source document.

---

# PHASE 10 — Evaluation Benchmark
**"Measure everything before claiming improvement."**

### Goal
Establish an automated evaluation harness to measure the precision, recall, and overall quality of our extraction pipeline (Docling vs others) against a known gold standard.

### Step-by-Step Implementation Plan

#### Step 10A: Ground Truth Schema and Data
**Objective:** Define the structure for our gold standard data.
1. Create `backend/tests/benchmarks/data/gold_standard.json`.
2. Define expected outcomes for a dummy test document (e.g. expected number of formulas, specific entities that must be found, heading hierarchy).

#### Step 10B: Implement Evaluator Metrics
**Objective:** Write Python scripts to calculate F1, Precision, and Recall.
1. Create `backend/tests/benchmarks/evaluator.py`.
2. Implement functions to compare an ingestion job's final S3 artifacts (`entities.json`, `formulas.json`, `canonical.json`) against the gold standard JSON.
3. Calculate:
   - Entity Precision/Recall/F1
   - Formula Extraction % (Recall)
   - Hierarchy Depth Match

#### Step 10C: Benchmark Runner
**Objective:** Provide a CLI tool to run the benchmark end-to-end.
1. Create `backend/tests/benchmarks/run_eval.py`.
2. The script should:
   - Trigger a full ingestion pipeline for the test PDF.
   - Wait for completion.
   - Run the `evaluator.py` logic over the resulting artifacts.
   - Output a beautiful Markdown table of the results.

### Acceptance Criteria
- ✅ Benchmark runs without human intervention via `python -m tests.benchmarks.run_eval`.
- ✅ Evaluator produces quantifiable metrics (P/R/F1) for extraction accuracy.
- ✅ Results answer definitively how well the system performs on complex academic PDFs.

---

## Phase Dependency Summary

```
Phase 1 (S3 Namespace)
    ↓
Phase 2 (Canonical AST + Docling)
    ↓
Phase 3 (Knowledge Extraction)
    ↓
Phase 4 (Inspection) ←── inspect as you build; don't wait until the end
    ↓
Phase 5 (Chunking + Staged Celery)
    ↓
Phase 6 (Analysis Framework + Summarization)
    ↓
Phase 7 (Unified Retriever)
    ↓
Phase 8 (Quiz / Formulas / PYQ)
    ↓
Phase 9 (Multi-doc / Comparison)
    ↓
Phase 10 (Evaluation)
```

## Files Changed Per Phase

| Phase | New Files | Modified Files | Migration |
|---|---|---|---|
| 1 | `artifact_manager.py`, `ingestion_job_model.py` | `document_model.py`, `document_service.py`, `cleanup_tasks.py`, `storage_repository.py` | ✅ |
| 2 | `docling_parser.py`, `quality_evaluator.py`, `ast_schema.py`, `ast_builder.py`, `hierarchy_engine.py` | `llama_parser.py`, `model_factory.py`, `pipeline.py`, `pyproject.toml` | ✅ |
| 3 | `formula_extractor.py`, `question_extractor.py`, `relation_extractor.py`, 3 `extracted_*_model.py` | `gliner_extractor.py`, `entity_resolver.py`, `graph_repository.py` | ✅ |
| 4 | `document_inspector.py`, `inspection_routes.py`, `debug.html` | `main.py` | ❌ |
| 5 | `ast_chunker.py` | `ingestion_tasks.py`, `vector_repository.py`, `pipeline.py` | ❌ |
| 6 | `analysis/base.py`, `analysis_job_model.py`, `document_summarizer.py`, `analysis_tasks.py`, `analysis_routes.py` | — | ✅ |
| 7 | `unified_retriever.py`, `qdrant_retriever.py`, `neo4j_retriever.py` | `query_routes.py` | ❌ |
| 8 | `quiz_generator.py`, `formula_revision.py`, `pyq_mapper.py` | `analysis_tasks.py`, `analysis_routes.py` | ❌ |
| 9 | `course_summarizer.py`, `document_comparator.py` | `analysis_tasks.py`, `analysis_routes.py` | ❌ |
| 10 | `tests/benchmarks/` (full suite) | — | ❌ |
