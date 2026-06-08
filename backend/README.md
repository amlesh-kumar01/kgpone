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
