import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, status
from fastapi.responses import StreamingResponse, JSONResponse
from src.services.ingestion.parser_service import parse_pdf

router = APIRouter()

# Data directories inside backend root
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
PARSED_DIR = BASE_DIR / "data" / "parsed"

# Ensure directories exist
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PARSED_DIR.mkdir(parents=True, exist_ok=True)

def process_and_save_notes(file_id: str, temp_pdf_path: Path, parsed_md_path: Path, filename: str):
    """
    Background task to run LlamaParse on the uploaded PDF, ingest it into Qdrant/Neo4j, and clean up.
    """
    try:
        # Parse using LlamaParse (blocks, but runs in the background thread)
        parsed_content = parse_pdf(temp_pdf_path)

        # Save the parsed markdown output
        with open(parsed_md_path, "w", encoding="utf-8") as f:
            f.write(parsed_content)

        # Triggers chunking, embedding, and vector/graph DB population
        from src.services.ingestion.ingestion_service import IngestionService
        ingestor = IngestionService()
        ingestor.ingest_parsed_markdown(file_id, parsed_content, {
            "title": filename,
            "course_code": "GEN101",
            "academic_year": "1st Year"
        })

    except Exception as e:
        # Log failure (we could write a status/error file to PARSED_DIR if needed)
        error_md_path = PARSED_DIR / f"{file_id}.error"
        with open(error_md_path, "w", encoding="utf-8") as f:
            f.write(f"Parsing failed: {str(e)}")

    finally:
        # Clean up temp PDF to save disk space
        if temp_pdf_path.exists():
            os.remove(temp_pdf_path)

@router.get("/{workspace_id}/stream")
def stream_agent(workspace_id: str):
    def fake_stream():
        yield "data: Hello\n\n"
    return StreamingResponse(fake_stream(), media_type="text/event-stream")

@router.post("/upload-notes", status_code=status.HTTP_202_ACCEPTED)
async def upload_notes(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Endpoint to upload a PDF file. Triggers parsing asynchronously in the background.
    Returns the file_id immediately.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_id = str(uuid.uuid4())
    temp_pdf_path = UPLOADS_DIR / f"{file_id}.pdf"
    parsed_md_path = PARSED_DIR / f"{file_id}.md"

    try:
        # Save uploaded PDF to temp location
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Add parsing to background tasks
        background_tasks.add_task(
            process_and_save_notes,
            file_id=file_id,
            temp_pdf_path=temp_pdf_path,
            parsed_md_path=parsed_md_path,
            filename=file.filename
        )

        return {
            "file_id": file_id,
            "status": "processing",
            "filename": file.filename
        }

    except Exception as e:
        # Clean up if saving the file itself fails before task starts
        if temp_pdf_path.exists():
            os.remove(temp_pdf_path)
        raise HTTPException(status_code=500, detail=f"Failed to initiate upload: {str(e)}")

@router.get("/notes/{file_id}")
async def get_parsed_notes(file_id: str):
    """
    Endpoint to retrieve the parsed markdown text for a given file_id.
    Returns 202 if still processing, 200 if completed, or 404/500 on error.
    """
    parsed_md_path = PARSED_DIR / f"{file_id}.md"
    temp_pdf_path = UPLOADS_DIR / f"{file_id}.pdf"
    error_path = PARSED_DIR / f"{file_id}.error"

    # 1. Check if processing has completed successfully
    if parsed_md_path.exists():
        try:
            with open(parsed_md_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {
                "file_id": file_id,
                "status": "completed",
                "content": content
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading parsed notes: {str(e)}")

    # 2. Check if processing failed with an error
    if error_path.exists():
        try:
            with open(error_path, "r", encoding="utf-8") as f:
                error_msg = f.read()
            # Clean up error file
            os.remove(error_path)
            raise HTTPException(status_code=500, detail=f"Parsing task failed: {error_msg}")
        except Exception as e:
            if "Parsing task failed" in str(e):
                raise
            raise HTTPException(status_code=500, detail=f"Error reading failure log: {str(e)}")

    # 3. Check if file is still processing (PDF exists in upload folder)
    if temp_pdf_path.exists():
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "file_id": file_id,
                "status": "processing"
            }
        )

    # 4. Otherwise, the file ID does not exist
    raise HTTPException(status_code=404, detail="Notes not found for the given ID.")
