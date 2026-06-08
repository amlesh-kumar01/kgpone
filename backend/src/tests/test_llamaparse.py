import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def main():
    pdf_path = Path("test_materials.pdf")
    output_path = Path("llamaparse_output.md")

    if not pdf_path.exists():
        print(f"[-] ERROR: '{pdf_path}' not found in current directory.", file=sys.stderr)
        sys.exit(1)

    api_key = os.environ.get("LLAMA_CLOUD_API_KEY")
    if not api_key:
        print("[-] WARNING: LLAMA_CLOUD_API_KEY not found in environment variables. LlamaParse will fall back to local/default keys if available.", file=sys.stderr)

    print("[*] Initializing LlamaParse client...")
    try:
        from llama_parse import LlamaParse
    except ImportError:
        print("[-] ERROR: llama-parse is not installed. Please run `uv add llama-parse` first.", file=sys.stderr)
        sys.exit(1)

    # Optimization for math and LaTeX
    math_instructions = (
        "The provided document contains complex mathematical and thermodynamic equations, tables, and multi-column layouts. "
        "Identify all mathematical expressions, equations, and inline math, and format them clearly in standard LaTeX "
        "(e.g., using $$ for block equations or $ for inline math). Ensure tables are extracted as markdown tables."
    )

    parser = LlamaParse(
        api_key=api_key,
        result_type="markdown",
        parsing_instruction=math_instructions,
        verbose=True
    )

    print("[*] Sending file to LlamaParse cloud for extraction...")
    try:
        documents = parser.load_data(str(pdf_path))
        print("[+] Cloud processing finished successfully.")

        if not documents:
            print("[-] WARNING: No content returned from LlamaParse.", file=sys.stderr)
            sys.exit(1)

        # Concatenate text from all returned document pages
        full_text = "\n\n".join([doc.text for doc in documents])

        print(f"[*] Saving parsed markdown to {output_path}...")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"[+] Successfully saved output to {output_path}!")

    except Exception as e:
        print(f"[-] ERROR during LlamaParse cloud execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
