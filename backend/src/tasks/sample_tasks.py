import os
import time
from pathlib import Path
from src.tasks.celery_app import celery_app
from src.services.ingestion.parser_service import parse_pdf

@celery_app.task(name="tasks.add_numbers")
def add_numbers(x: int, y: int) -> int:
    """
    A sample Celery task that adds two numbers, simulating a delay.
    """
    time.sleep(2)  # Simulate some processing delay
    return x + y

@celery_app.task(name="tasks.process_document_notes")
def process_document_notes(file_id: str, temp_pdf_path_str: str, parsed_md_path_str: str) -> dict:
    """
    Celery task to run LlamaParse on an uploaded PDF.
    Takes paths as strings for JSON serialization compatibility in Celery.
    """
    temp_pdf_path = Path(temp_pdf_path_str)
    parsed_md_path = Path(parsed_md_path_str)
    
    # Ensure parent directory for the output markdown exists
    parsed_md_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Parse using LlamaParse (runs in Celery worker thread/process)
        parsed_content = parse_pdf(temp_pdf_path)

        # Save the parsed markdown output
        with open(parsed_md_path, "w", encoding="utf-8") as f:
            f.write(parsed_content)

        return {"file_id": file_id, "status": "completed"}

    except Exception as e:
        # Log failure with an error file
        error_md_path = parsed_md_path.parent / f"{file_id}.error"
        with open(error_md_path, "w", encoding="utf-8") as f:
            f.write(f"Parsing failed: {str(e)}")
        raise e

    finally:
        # Clean up temp PDF to save disk space
        if temp_pdf_path.exists():
            os.remove(temp_pdf_path)
