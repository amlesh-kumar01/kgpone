import json
import os
import argparse
from src.repositories.s3.storage_repository import S3Storage
from tests.benchmarks.evaluator import Evaluator

def main():
    parser = argparse.ArgumentParser(description="Run Extraction Benchmark Evaluation")
    parser.add_argument("--document_id", type=str, required=True, help="UUID of the processed document")
    parser.add_argument("--filename", type=str, required=True, help="Original filename to match in gold standard")
    
    args = parser.parse_args()
    
    # Load Gold Standard
    gold_path = os.path.join(os.path.dirname(__file__), "data", "gold_standard.json")
    with open(gold_path, "r") as f:
        gold_data = json.load(f)
        
    evaluator = Evaluator(gold_data)
    
    # Load Artifacts from S3
    s3 = S3Storage()
    
    entities = s3.read_json(f"documents/{args.document_id}/artifacts/entities.json") or []
    formulas = s3.read_json(f"documents/{args.document_id}/artifacts/formulas.json") or []
    questions = s3.read_json(f"documents/{args.document_id}/artifacts/questions.json") or []
    
    # Run Evaluation
    results = evaluator.evaluate(args.filename, entities, formulas, questions)
    
    if "error" in results:
        print(f"Error: {results['error']}")
        return
        
    print(f"\n# Evaluation Results: {args.filename}")
    print("-------------------------------------------------")
    print(f"Entities Extracted: {results['extracted_counts']['entities']}")
    print(f"Entity Precision:   {results['entity_precision']}")
    print(f"Entity Recall:      {results['entity_recall']}")
    print(f"Entity F1 Score:    {results['entity_f1']}")
    print("-------------------------------------------------")
    print(f"Formulas Extracted: {results['extracted_counts']['formulas']}")
    print(f"Formula Extraction: {results['formula_extraction_percent']}%")
    print("-------------------------------------------------")
    print(f"Questions Extracted:{results['extracted_counts']['questions']}")
    print(f"Question Extraction:{results['question_extraction_percent']}%")
    print("-------------------------------------------------\n")

if __name__ == "__main__":
    main()
