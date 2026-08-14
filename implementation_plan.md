# KGPOne — Core Education + AI Engine
## Architecture Proposal

> **Framing:** KGPOne is not a generic SaaS management platform. It is a **reusable education + AI engine** that powers different institutional builds. The engine is shared. Institution-specific workflows, terminology, and UI are custom code built on top of the engine \u2014 not configuration flags.

---

## 1. The Four-Layer Academic Model

Every educational institution — regardless of type — organises its academic content into exactly **four layers** below the institution itself. The layers are universal; only the terminology changes.

```
Institution
  └── Layer 1: OrganizationalUnit   ← the top-level grouping within the institution
        └── Layer 2: Offering         ← the time-bound or cohort-bound container
              └── Layer 3: StudyUnit   ← the subject / module being taught
                    └── Layer 4: LearningResource  ← the actual material
```

### Mapping Across Institution Types

| Layer | Generic Name | Coaching Institute | College / University | EdTech Platform | School |
|---|---|---|---|---|---|
| **1** | OrganizationalUnit | Division (JEE / NEET / UPSC) | Department (CSE / EC) | Exam / Class type | Grade / Class |
| **2** | Offering | Batch (2025 Batch, Dropper Batch) | Year Batch (2022–23) | Timeline Class | Section or Timeline |
| **3** | StudyUnit | Subject (Physics / Chemistry) | Subject (DBMS / OS) | Subject | Subject |
| **4** | LearningResource | DPP, Test Paper, Video | Notes, PYQ, Slides | Lesson, Quiz | Worksheet, Textbook chapter |

The structure is **identical**. What differs across institution types is the label for each layer and the workflows built on top.

### The Central Insight: Rename Tables to Match the Four Layers

To make the engine truly generic and decouple it from IIT KGP's specific history, we will **rename the core database tables** to match this universal four-layer model. 

The renaming strategy:
```
departments        →  organizational_units
course_offerings   →  offerings
courses            →  study_units
documents          →  learning_resources
```

> **Note on ordering:** In the current IIT KGP schema, `course_offerings` is a child of `courses` (a course is offered in a semester). In the generic 4-layer model, Offering (Layer 2) sits *above* StudyUnit (Layer 3) — a batch *contains* subjects, not the other way around. For IIT KGP this distinction is subtle (a CourseOffering IS a subject in a semester), so the existing FK is fine as-is. For coaching and school builds, `course_offerings` should be read as "the batch/section this subject belongs to."

**Coaching example:**
- `departments` → Division (JEE Advanced)
- `course_offerings` → Batch (Target 2026 — JEE Advanced)
- `courses` → Subject (Physics)
- `documents` → DPP Set 12, Mock Test 4, Inorganic Chemistry Notes

**School example:**
- `departments` → Grade (Class 10)
- `course_offerings` → Section (Class 10 — Section A, 2024–25)
- `courses` → Subject (Mathematics)
- `documents` → Chapter 3 worksheet, Board exam paper 2023

**College example:**
- `departments` → Department (CSE)
- `course_offerings` → Year Batch cohort (2022 batch) or Semester offering
- `courses` → Subject (DBMS, Operating Systems)
- `documents` → Lecture notes, PYQ, Assignment

The structure maps perfectly. What differs is only the label for each layer and the workflows built on top.

### What This Means for the Plan

The most powerful realization is that **we don't need terminology configuration at all.** 

If a user names an `organizational_unit` "Class 10" or "JEE Division", the frontend simply displays that name on a card. The UI doesn't need to inject the word "Grade:" or "Division:" in front of it. By keeping the schema generic, the engine becomes completely independent of the organization type.

The right approach is to clean up the schema so it is undeniably generic:

1. Add **one new table**: `institutions` (minimal — slug + feature flags)
2. **Rename** the four core tables to `organizational_units`, `offerings`, `study_units`, and `learning_resources`.
3. Add **`institution_id` FK** to all these tables.
4. **Remove terminology config entirely.** The UI is built around generic containers and simply renders the names the users provide.
5. Institution-specific workflows (like a Rank Predictor for coaching) live in custom route handlers built on the shared engine, checking the institution's feature flags.

---

## 2. What KGPOne Actually Is: An Engine, Not a Platform

```
┌──────────────────────────────────────────────────────────────────────┐
│                         KGPOne Core Engine                          │
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│  │  Knowledge      │  │  RAG + Query     │  │  Academic          │  │
│  │  Ingestion      │  │  Engine          │  │  Structure         │  │
│  │  Pipeline       │  │                  │  │  (generic tables)  │  │
│  │                 │  │  Plan → Retrieve │  │                    │  │
│  │  Parse → AST    │  │  → Rerank        │  │  org_units         │  │
│  │  → Extract      │  │  → Generate      │  │  study_units       │  │
│  │  → Chunk        │  │  → Stream        │  │  offerings         │  │
│  │  → Embed        │  │                  │  │  learning_resources│  │
│  │  → Index        │  │  Semantic cache  │  │  users             │  │
│  └─────────────────┘  └──────────────────┘  └────────────────────┘  │
│                                                                      │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐  │
│  │  Assessment     │  │  Chat + Memory   │  │  Infrastructure    │  │
│  │  Primitives     │  │  Engine          │  │  Adapters          │  │
│  │                 │  │                  │  │                    │  │
│  │  SUMMARIZE      │  │  Conversations   │  │  Qdrant / Neo4j    │  │
│  │  QUIZ           │  │  User memory     │  │  S3 / Redis        │  │
│  │  QUESTION_GEN   │  │  MCP server      │  │  LLMFactory        │  │
│  └─────────────────┘  └──────────────────┘  └────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
  ┌─────────────┐         ┌──────────────┐        ┌──────────────┐
  │  IIT KGP    │         │  JEE Coaching│        │  School      │
  │  Build      │         │  Build       │        │  Build       │
  │             │         │              │        │              │
  │  PYQ routes │         │  Batch routes│        │  Grade routes│
  │  Semester UI│         │  Target exam │        │  Section UI  │
  │  Faculty UI │         │  DPP upload  │        │  Teacher UI  │
  │  Credits    │         │  Rank pred.  │        │  Curriculum  │
  └─────────────┘         └──────────────┘        └──────────────┘
```

The **engine** is shared, deployed once (or per institution for isolation). The **institutional build** is custom FastAPI routes + React frontend that calls the engine APIs using the institution's own terminology and workflows. The database schema is the same across all builds.

---

## 3. The Minimal Database Changes Required

Only two actual schema changes are needed. Everything else stays the same.

### Change 1: Add `institutions` table

```sql
CREATE TABLE institutions (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug             VARCHAR(50) UNIQUE NOT NULL,  -- 'iit-kgp', 'allen-kota', 'dps-delhi'
  display_name     VARCHAR(255) NOT NULL,
  
  -- Feature package: which engine capabilities are enabled
  features         JSONB NOT NULL DEFAULT '{}',
  -- {"package": "university", "formula_extraction": true, "graph_enabled": true,
  --  "analysis_types": ["SUMMARIZE", "QUIZ", "PYQ_MAPPING"]}
  
  -- AI config: provider and model preferences + system prompt override
  ai_config    JSONB NOT NULL DEFAULT '{}',
  -- {"llm_provider": "gemini", "llm_model": "gemini-2.5-flash",
  --  "system_prompt": null}  <- null means use platform default
  
  -- Infrastructure routing (operator-only)
  infra_config JSONB NOT NULL DEFAULT '{}',
  -- {"qdrant_collection": "iit_kgp_docs", "s3_prefix": "institutions/iit-kgp",
  --  "redis_prefix": "iit_kgp", "neo4j_db": "iit_kgp"}
  
  tier         VARCHAR(20) NOT NULL DEFAULT 'shared',
  is_active    BOOLEAN NOT NULL DEFAULT true,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Change 2: Rename Tables, Standardize Identifiers, and Add `institution_id` FK

A single Alembic migration will handle renaming the tables, standardizing the identity columns (`name` and `code` for every layer), updating foreign keys, and injecting the tenant ID:

```sql
-- 1. Rename tables to generic names
ALTER TABLE departments RENAME TO organizational_units;
ALTER TABLE courses RENAME TO study_units;
ALTER TABLE course_offerings RENAME TO offerings;
ALTER TABLE documents RENAME TO learning_resources;

-- 2. Standardize 'name' and 'code' across all layers
-- organizational_units already has 'name' and 'code'
ALTER TABLE study_units RENAME COLUMN title TO name;
-- offerings previously only had 'year' and 'semester'
ALTER TABLE offerings ADD COLUMN name VARCHAR(255);
ALTER TABLE offerings ADD COLUMN code VARCHAR(50);
-- (Data migration step: set offering name to "Semester {semester} {year}")

-- 3. Rename foreign key columns to match
ALTER TABLE study_units RENAME COLUMN department_id TO org_unit_id;
ALTER TABLE offerings RENAME COLUMN course_id TO study_unit_id;
ALTER TABLE learning_resources RENAME COLUMN course_offering_id TO offering_id;
ALTER TABLE faculty_info RENAME COLUMN course_offering_id TO offering_id;

-- 4. Add nullable institution_id to all tables
ALTER TABLE organizational_units ADD COLUMN institution_id UUID REFERENCES institutions(id);
ALTER TABLE study_units          ADD COLUMN institution_id UUID REFERENCES institutions(id);
ALTER TABLE offerings            ADD COLUMN institution_id UUID REFERENCES institutions(id);
ALTER TABLE learning_resources   ADD COLUMN institution_id UUID REFERENCES institutions(id);
ALTER TABLE users                ADD COLUMN institution_id UUID REFERENCES institutions(id);
ALTER TABLE conversations        ADD COLUMN institution_id UUID REFERENCES institutions(id);

-- 5. Backfill: seed the IIT KGP institution record first, then update all rows
UPDATE organizational_units SET institution_id = (SELECT id FROM institutions WHERE slug = 'iit-kgp');
UPDATE study_units          SET institution_id = (SELECT id FROM institutions WHERE slug = 'iit-kgp');
UPDATE offerings            SET institution_id = (SELECT id FROM institutions WHERE slug = 'iit-kgp');
UPDATE learning_resources   SET institution_id = (SELECT id FROM institutions WHERE slug = 'iit-kgp');
UPDATE users                SET institution_id = (SELECT id FROM institutions WHERE slug = 'iit-kgp');
UPDATE conversations        SET institution_id = (SELECT id FROM institutions WHERE slug = 'iit-kgp');

-- 6. After backfill, make NOT NULL
ALTER TABLE organizational_units ALTER COLUMN institution_id SET NOT NULL;
-- ... (same for others)
```

### Change 3: User membership (optional, only if multi-institution users needed)

```sql
-- Only needed if a user can belong to multiple institutions (e.g., faculty at two)
-- For most deployments, institution_id on users is sufficient
CREATE TABLE user_institution_memberships (
  user_id        UUID REFERENCES users(id),
  institution_id UUID REFERENCES institutions(id),
  role           VARCHAR(20) NOT NULL,  -- ADMIN | PUBLISHER | STUDENT
  is_active      BOOLEAN NOT NULL DEFAULT true,
  PRIMARY KEY (user_id, institution_id)
);
```

**That is the complete database change.** No table renames. No new entity models. No schema redesign.

---

## 4. Engine Layer Boundaries

The engine exposes clean internal service APIs. Institutional builds call these services directly. The engine does not know about institutional terminology or workflows.

### 4.1 Knowledge Ingestion Engine
**What it does:** Takes any document and produces a queryable knowledge artifact.
**What it does NOT know:** Whether the document is a "PYQ" or a "DPP" or a "Worksheet" \u2014 that's metadata stored on `documents.doc_type` and interpreted by the institutional build.

```
Engine Input:  file_path + document_id + offering_id + parsing_instructions
Engine Output: vectors in Qdrant + nodes in Neo4j + artifacts in S3 + metadata in Postgres

Engine is ignorant of:
  - What "offering_id" represents (semester offering / batch / section)
  - What "doc_type" means to the institution
  - What language the institution uses for any of this
```

### 4.2 RAG Query Engine
**What it does:** Takes a query and a scope (optional offering_id), retrieves context, generates a grounded answer.
**What it does NOT know:** Whether it's answering a JEE student or an IIT professor.

```
Engine Input:  query + offering_id? + document_ids? + ai_config
Engine Output: streamed answer + citations + sources + intent

Engine is ignorant of:
  - Institution type
  - What "course_code" means to the caller
  - Whether PYQ mode or formula mode or general mode is "special"
    (those are just intent variants handled by the planner)
```

### 4.3 Assessment Engine
**What it does:** Generates structured assessments from indexed documents.
**What it does NOT know:** Whether it's generating "quiz questions" or "test papers" or "DPP problems."

```
Engine Input:  document_id + assessment_type + parameters
Engine Output: structured question set (JSON) + explanation + answer key
```

### 4.4 Academic Structure Engine
**What it does:** CRUD over `organizational_units`, `study_units`, `offerings`, `learning_resources`. 
Every unit across all 3 structural layers now has a standard **`name`** and **`code`** column. This standardizes search and indexing across thousands of generic units.
**What it exposes to builds:** Generic endpoints that can be called with institution-appropriate payloads. The engine validates the data model but doesn't interpret what the records mean.

---

## 5. How Institutional Builds Work

Each institutional build is a thin layer of custom code on top of the engine. It can be:
- **Same codebase, different routes mounted conditionally** (for rapid development)
- **Separate FastAPI app that imports engine services** (for full isolation)
- **Same codebase, institution-aware feature flags** (simplest)

### Example: IIT KGP Build (current)

The existing `academic_routes.py`, `document_routes.py`, `query_routes.py` ARE the IIT KGP build. They're already there. No changes needed for this institution.

The IIT KGP build:
- Uses `SemesterType.AUTUMN/SPRING/SUMMER` for offerings
- Calls documents "Lecture Slides", "PYQs", "Notes", "Syllabus"
- Has a `PYQ_MAPPING` analysis type
- Uses "Faculty" and "TA" terminology
- Shows credits on course cards

All of this is already implemented and continues working unchanged.

### Example: JEE Coaching Build (what you'd add)

A new `coaching_routes.py` that:
- Uses the generic API to fetch `organizational_units` (which happen to be named "JEE Advanced", "NEET" by the admin).
- Uses the generic API to fetch `offerings` (named "Target 2025" or "Morning Batch").
- Adds `/api/v1/coaching/batches/{id}/rank-prediction` (custom endpoint)
- Adds `/api/v1/coaching/test-analysis` (custom workflow using assessment engine)
- Has its own frontend that shows "Target Exam", "Days Left", "Rank Estimate"
- Uses the exact same underlying generic tables.

The JEE coaching build shares 100% of the engine (ingestion, RAG, assessment, chat). It adds ~5 custom route files and a custom frontend. Zero DB schema changes beyond the initial rename.

### Example: School Build

A new `school_routes.py` that:
- Calls `organizational_units` → "Grades"
- Calls `study_units` → "Subjects"
- Calls `offerings` → "Sections"
- Has curriculum mapping features (custom service using engine + custom tables if needed)
- Has parent-teacher communication (custom, built alongside)
- Has simple quiz feature (uses assessment engine primitives)

Same engine. Custom build on top.

---

## 6. Institution Configuration (Minimal & Practical)

Because we have embraced a purely generic schema, we **do not need any terminology mapping**. 

The UI does not need to know whether to call a container a "Grade", a "Department", or a "Division". It simply displays the user-provided name (e.g., a card titled "Class 10"). This completely eliminates the need for the platform to know what *type* of institution it is serving.

The only configuration an institution needs is which engine capabilities are enabled (`institutions.features`):

```json
{
  "package": "standard",
  "rag_enabled": true,
  "chat_enabled": true,
  "assessment_enabled": true,
  "formula_extraction": false,
  "graph_enabled": false,
  "pdf_annotator": false,
  "byok_enabled": false,
  "mcp_enabled": false,
  "analysis_types": ["SUMMARIZE", "QUIZ"]
}
```

### Feature Packages (sensible defaults)

| Package | Who it's for | What's on |
|---|---|---|
| `basic` | Simple document library | Ingestion, search, document viewer |
| `standard` | Most institutions **(default)** | Basic + RAG Q&A, chat, quiz gen, summarize |
| `test_prep` | Coaching / competitive exam | Standard + PYQ mapping, test analysis, formula extraction |
| `university` | Universities / IITs | test_prep + graph RAG, PDF annotator, BYOK, MCP, cross-doc analysis |
| `custom` | Operator-defined | Any flags directly |

### System Prompt (Default + Override)

Default system prompt used when `ai_config.system_prompt` is null:

```
You are an intelligent academic assistant for {institution_name}.
You help students understand course material and answer questions
grounded in the documents uploaded to this platform.

Rules:
- Ground your answers in the provided document context.
- Cite sources with [CIT-N] notation when context is used.
- If the answer is not in the context, say so clearly.
- Be concise for factual questions; thorough for conceptual ones.
- Use clear notation for mathematical or technical content.
```

`{institution_name}` is substituted at runtime using `request.state.institution.display_name`.

---

## 7. Infrastructure Isolation Per Institution

Different institutions need different levels of isolation depending on data sensitivity and performance requirements.

### Isolation via Naming Conventions (No Architecture Change)

All infrastructure isolation uses **naming conventions**, not separate instances, for the shared tier:

```python
# From institution infra_config
qdrant_collection = infra_config.get("qdrant_collection", f"{slug}_documents")
s3_prefix        = infra_config.get("s3_prefix", f"institutions/{slug}")
redis_prefix     = infra_config.get("redis_prefix", slug)
neo4j_db         = infra_config.get("neo4j_db", f"{slug}_graph")
```

**Qdrant:** Each institution gets its own named collection (`iit_kgp_documents`, `allen_kota_documents`). Cross-institution vector search is architecturally impossible.

**S3:** Each institution's files live under `institutions/{slug}/documents/{doc_id}/`. Presigned URL generation validates the key prefix before signing.

**Redis:** All cache keys prefixed with institution slug: `iit_kgp:cache:...`, `allen_kota:cache:...`

**Neo4j:** Each institution uses its own named database (`iit_kgp`, `allen_kota`). The `InfrastructureRegistry` routes the session accordingly.

**PostgreSQL:** `institution_id` FK on all tables means every query is automatically scoped. The engine's service layer always includes `institution_id` in WHERE clauses.

### Celery Worker Isolation

```
shared-tier queue:    "ingestion.shared"   ← all shared institutions
dedicated-tier queue: "ingestion.iit_kgp"  ← dedicated institution workers
```

Workers are configured by which queues they consume.

---

## 8. Tenant Resolution (Minimal Middleware)

A single lightweight middleware resolves the institution before every request:

```python
class InstitutionMiddleware:
    """
    Resolves institution from:
      1. Subdomain: iit-kgp.yourdomain.com → slug "iit-kgp"
      2. JWT claim: token.institution_id
      3. Header: X-Institution-Slug (for machine clients / dev)
    
    Injects request.state.institution (InstitutionContext dataclass).
    Caches institution config in Redis for 5 minutes.
    """
```

The `InstitutionContext` is a lightweight dataclass \u2014 not a database session, not a connection pool. It's resolved once per request and contains the slug, display_name, features, ai_config, and infra_config.

The JWT token gets one additional claim: `institution_id`. Login now scopes the user to their institution.

---

## 9. What Must NOT Change

These parts of the engine are correct and should be left entirely alone:

| Component | Why It's Already Right |
|---|---|
| Celery task pipeline (PARSE → EMBED → INDEX) | Correct architecture for async document processing |
| AST canonical format (`ast_schema.py`) | Good universal document representation |
| `LLMFactory` provider dispatch | Already provider-agnostic, just needs `ai_config` param |
| `BaseRetriever / BaseReranker / BaseAnswerGenerator` | Clean abstractions, keep them |
| `ArtifactManager` S3 key convention | Just update the prefix calculation |
| Alembic migration system | The right tool, keep using it |
| `StandardResponse` schema | Good API contract |
| JWT auth system | Correct, just add `institution_id` claim |
| `IVectorRepo / ILLMFactory` interfaces | Good decoupling, preserve |

---

## 10. Migration Plan (4 Phases, Minimal Risk)

IIT KGP remains fully functional throughout. Each phase is independently reversible.

---

### Phase 0 \u2014 Stability (Now → Week 1)
Fix active bugs. No architectural changes.
- [x] Fix `build_chunks_task` `AttributeError` (done)
- [ ] Fix type guards in `ast_chunker.py`
- [ ] Fix `allow_origins=["*"]` CORS in production
- [ ] Clean up `debug_s3.py` and other dev artifacts from repo

---

### Phase 1 \u2014 Institution Foundation (Week 1\u20133)
**Zero breaking changes. Purely additive.**

- [ ] Add `institutions` table (Alembic migration)
- [ ] Rename existing core tables to generic names (`organizational_units`, `study_units`, `offerings`, `learning_resources`) and update FK columns
- [ ] Seed IIT KGP institution record with slug `iit-kgp`
- [ ] Add `institution_id` nullable FK to all core tables
- [ ] Backfill all existing rows with the IIT KGP institution ID
- [ ] Make `institution_id` NOT NULL after backfill
- [ ] Add `InstitutionMiddleware` (sets `request.state.institution` but does NOT yet enforce it)
- [ ] Add `institution_id` to JWT claims at login
- [ ] Cache institution config in Redis

**Validation:** IIT KGP works exactly as before. No route changes, no service changes.

---

### Phase 2 \u2014 Enforce Scoping in Engine Queries (Week 3\u20136)
**Adds data isolation. Low risk if tested carefully.**

- [ ] All service-layer queries add `institution_id == request.state.institution.id` filter
- [ ] Presigned S3 URLs validate institution key prefix before signing
- [ ] Qdrant search routes to institution-specific collection (create `iit_kgp_documents`, re-embed if needed or migrate)
- [ ] Redis cache keys prefixed with institution slug
- [ ] Neo4j session uses institution-specific database
- [ ] `LLMFactory.get_llm()` accepts `InstitutionAIConfig` from `request.state.institution`
- [ ] System prompt filled from institution `ai_config.system_prompt` (with default fallback)
- [ ] Celery tasks receive and validate `institution_id` in payload

**Validation:** Create a test institution (`slug: "test-school"`), verify its queries don't return IIT KGP data, and vice versa.

---

### Phase 3 \u2014 Second Institution Build (Week 6\u201312)
**Proves the engine architecture works for a different use case.**

- [ ] Build `coaching_routes.py` on top of the engine for a JEE/NEET coaching use case
- [ ] Institution onboarding CLI: `python -m kgpone.admin provision --slug allen-kota --config allen.json`
  - Creates institution record
  - Creates Qdrant collection
  - Creates Neo4j database
  - Seeds admin user
- [ ] Institution admin UI: configure terminology, features, system prompt
- [ ] Validate isolation between `iit-kgp` and the new institution

**This is the proof of concept.** If a second institution can be onboarded in under an hour using different terminology and workflows without touching the engine, the architecture is correct.

---

### Phase 4 \u2014 Hardening (Week 12\u201316)
- [ ] Rate limiting per institution
- [ ] Structured logging with `institution_id` field
- [ ] Backup strategy per institution
- [ ] OpenTelemetry traces
- [ ] Load test: 3+ institutions with concurrent ingestion + queries

---

## 11. Answering: What Changed vs. Previous Plan?

| Decision | Previous Plan | This Plan | Reason |
|---|---|---|---|
| Table names | Keep existing names | **Rename them** | A generic engine should have a generic schema, removing IIT KGP bias. |
| Domain abstraction | New generic entity hierarchy | **Existing hierarchy IS the generic hierarchy** | The current parent-child structure captures the universal pattern perfectly. |
| DB migrations | Minimal (FK only) | **Table renames + `institutions` table + `institution_id` FK** | A clean, one-time structural alignment. |
| Terminology Config | Hardcoded Enum / JSON mapping | **Removed Entirely** | The UI simply renders the names the admin typed (e.g. "Math Dept" or "Class 10"). Completely decouples the engine from organization types. |

---

## 12. Summary: What KGPOne Becomes

```
KGPOne Core Engine
├── Knowledge Ingestion Pipeline  (shared, institution-agnostic)
├── RAG + Query Engine            (shared, parameterized by ai_config)
├── Assessment Primitives         (shared, institution-agnostic)
├── Chat + Memory Engine          (shared, scoped by institution_id)
├── Academic Structure API        (shared, generic tables)
└── Infrastructure Adapters       (shared, routed by infra_config)

IIT KGP Build (current codebase, unchanged)
├── PYQ workflows
├── Semester-based offering UI
├── Formula revision analysis
└── Faculty + credits UI

JEE Coaching Build (to be added)
├── Batch management routes
├── Target exam + rank analytics
├── DPP upload + test analysis
└── Custom frontend

School Build (future)
├── Grade/Section management
├── Curriculum mapping
└── Parent communication
```

The engine is one codebase. Each build is a thin layer on top. Deployments are isolated by `institution_id` in data and by naming convention in infrastructure. Database tables don't change. The IIT KGP deployment keeps working exactly as-is.
