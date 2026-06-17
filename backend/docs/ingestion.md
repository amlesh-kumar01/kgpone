# The Modular Ingestion Pipeline

The document ingestion pipeline processes PDFs using modern Generative AI tooling inside a background Celery worker.

## The Flow
1. **Upload Initiation**: User requests a presigned URL via `POST /api/v1/documents/presigned-url`.
2. **Direct AWS Transfer**: User uploads the PDF directly from the browser to the S3 bucket to bypass backend latency.
3. **Database Insertion**: User calls `POST /api/v1/documents/` with the metadata and the S3 key. This writes to PostgreSQL with `status="PENDING"` and fires off a Celery Task.
4. **Celery Worker Execution** (`process_document_task`):
   - **Download**: Pulls the file from S3 to local `/tmp`.
   - **Parser Layer** (`LlamaParserImpl`): Passes the PDF to LlamaParse (Vision LLM). The pipeline dynamically builds a prompt using the Course details (e.g. `CS101: Autumn 2026`) + user's custom `parsing_instructions` to guarantee accurate LaTeX equations and markdown table extraction.
   - **Chunker Layer** (`RecursiveChunker`): Splits the returned Markdown intelligently on Headers and recursive characters to preserve semantic sections.
   - **Metadata Builder**: Scrapes PostgreSQL for relational data and flattens it.
   - **Embedder Layer** (`GeminiEmbedder`): Calls Google's Gemini `text-embedding-004` to generate dense vectors.
   - **Vector Store Layer** (`QdrantRepository`): Appends the flattened metadata directly onto the vector payload and upserts the points into the `documents` collection.
5. **Completion**: Updates the document in Postgres to `status="COMPLETED"`.
