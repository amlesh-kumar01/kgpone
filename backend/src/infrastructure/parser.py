import os
from pathlib import Path
from llama_parse import LlamaParse

def parse_pdf(file_path: str) -> str:
    """
    Parses a PDF using LlamaParse and returns the complete parsed markdown content.
    """
    api_key = os.environ.get("LLAMA_CLOUD_API_KEY")
    if not api_key:
        raise ValueError("LLAMA_CLOUD_API_KEY is not set in environment variables.")

    # Optimization instructions to format equations and preserve all content
    math_instructions = (
        "The provided document contains complex mathematical and thermodynamic equations, tables, and multi-column layouts. "
        "Extract the entire text and content of the document in full. "
        "Ensure all mathematical expressions, equations, and inline math are formatted clearly in standard LaTeX "
        "(e.g., using $$ for block equations or $ for inline math). Keep all tables formatted in standard markdown tables."
    )

    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        parsing_instruction=math_instructions,
        verbose=True
    )

    # Convert path to string as expected by LlamaParse
    documents = parser.load_data(str(file_path))
    if not documents:
        raise RuntimeError("No content was returned from LlamaParse.")

    # Join the pages to form the full document content
    full_text = "\n\n".join([doc.text for doc in documents])
    return full_text
