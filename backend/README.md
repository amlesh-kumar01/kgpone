# KgpOne Backend Service

This is the FastAPI backend service for KnowledgeOS. It includes an asynchronous document ingestion pipeline powered by **LlamaParse** to parse PDF notes and extract clean Markdown text with full LaTeX mathematical notation.

---

## Setup & Running

### 1. Prerequisites
* [uv](https://github.com/astral-sh/uv) (Python package manager)
* LlamaParse Account (API Key)

### 2. Environment Configuration
Create a `.env` file in this directory and populate it with your LlamaParse key:
```env
LLAMA_CLOUD_API_KEY=your_llamaparse_api_key_here
```

### 3. Install Dependencies & Start Server
Run the FastAPI development server:
```bash
uv run uvicorn src.main:app --reload
```
The server will start at `http://localhost:8000`. You can access the interactive Swagger documentation at **`http://localhost:8000/docs`**.

---

## API Endpoints (Document Ingestion)

Because LlamaParse processing runs in the cloud and can take time on larger PDFs, the ingestion pipeline runs asynchronously using FastAPI's background tasks.

### 1. Ingest/Upload PDF Notes
Upload a PDF file to trigger parsing in the background.

* **Endpoint:** `POST /workspace/upload-notes`
* **Content-Type:** `multipart/form-data`
* **Body:** `file` (the PDF file)
* **Response Example:**
  ```json
  {
    "file_id": "fe90337e-2d6d-48ee-bf94-5e6a49b09298",
    "status": "processing",
    "filename": "lecture_notes.pdf"
  }
  ```

### 2. Retrieve Parsed Output (Polling)
Check the status or fetch the final LaTeX markdown output using the `file_id` returned during upload.

* **Endpoint:** `GET /workspace/notes/{file_id}`
* **Response (Still Processing - Status 202):**
  ```json
  {
    "file_id": "fe90337e-2d6d-48ee-bf94-5e6a49b09298",
    "status": "processing"
  }
  ```
* **Response (Completed - Status 200):**
  ```json
  {
    "file_id": "fe90337e-2d6d-48ee-bf94-5e6a49b09298",
    "status": "completed",
    "content": "# Lecture 1\n\nThis is text... $$\int_0^L \psi^2 \, dx = 1$$"
  }
  ```
* **Response (Failed - Status 500):**
  ```json
  {
    "detail": "Parsing task failed: <error message>"
  }
  ```

---

## API Endpoints (GraphRAG & Chat Query)

### 1. Execute Chat Query
Performs hybrid GraphRAG retrieval (semantic vector search in Qdrant + recursive prerequisite path traversal in Neo4j) to generate grounded tutor responses with citations.

* **Endpoint:** `POST /api/chat/query`
* **Headers:** Enforces security context authentication (expects HttpOnly JWT token cookies).
* **Body (JSON):**
  ```json
  {
    "query": "Explain A* search optimizations",
    "course_code": "CSE301"
  }
  ```
* **Response Example (Status 200):**
  ```json
  {
    "answer": "A* search uses evaluation f(n) = g(n) + h(n) [CIT-1]. Since you asked about optimization, note that A* search has a prerequisite Graph Theory Basics [CIT-2] in course MTH201...",
    "citations": [
      {
        "citation_id": "CIT-1",
        "source_title": "lecture_notes.pdf",
        "course_code": "CSE301",
        "academic_year": "3rd Year",
        "page_number": 1,
        "section": "A* Heuristic Search",
        "confidence": "High",
        "score": 0.892,
        "is_prerequisite": false,
        "prerequisite_concept": null,
        "text_snippet": "A* Search uses f(n)..."
      },
      {
        "citation_id": "CIT-2",
        "source_title": "discrete_math.pdf",
        "course_code": "MTH201",
        "academic_year": "2nd Year",
        "page_number": 4,
        "section": "Graph Basics",
        "confidence": "Medium",
        "score": 0.710,
        "is_prerequisite": true,
        "prerequisite_concept": "Graph Theory Basics",
        "text_snippet": "A graph is defined as G=(V,E)..."
      }
    ],
    "graph_visualization": {
      "nodes": [
        {
          "id": "A* Heuristic Search",
          "label": "A* Heuristic Search",
          "course": "CSE301",
          "type": "target"
        },
        {
          "id": "Graph Theory Basics",
          "label": "Graph Theory Basics",
          "course": "MTH201",
          "description": "Fundamental graph theory...",
          "type": "prerequisite"
        }
      ],
      "edges": [
        {
          "id": "edge_A* Heuristic Search_Graph Theory Basics",
          "source": "A* Heuristic Search",
          "target": "Graph Theory Basics",
          "label": "HAS_PREREQUISITE"
        }
      ]
    },
    "has_missing_prerequisites": true
  }
  ```

